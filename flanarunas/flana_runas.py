import asyncio
import json

import aiohttp
import flanautils
import jellyfish
from flanautils import RatioMatch

import constants
import process_utils
from exceptions import NoChampion
from models.champion import Champion
from models.rune_page import RunePage
from my_qt.app import MyQtApp


class FlanaRunas:
    def __init__(self):
        self.qt_app = MyQtApp()
        self.http_session: aiohttp.ClientSession | None = None
        self.champions: list[Champion] = []
        self.current_champion: Champion | None = None
        self.saved_rune_pages: dict[int, list] = self.load_data()
        self.base_url = ''
        self.is_lol_connected = False

        self.qt_app.connect_signals(self)

    def add_rune_page(self, rune_page: RunePage):
        champion_rune_pages = []
        is_new = True
        champion = self.get_page_rune_champion(rune_page)
        for saved_rune_page in self.saved_rune_pages.get(champion.id, []):
            if saved_rune_page.name == rune_page.name:
                champion_rune_pages.append(rune_page)
                is_new = False
            else:
                champion_rune_pages.append(saved_rune_page)

        if is_new:
            champion_rune_pages.append(rune_page)
            if champion.id not in self.saved_rune_pages:
                self.qt_app.combo_search.add_item(champion.name)

        self.saved_rune_pages[champion.id] = champion_rune_pages
        self.save_data()

    async def delete_rune_pages(self):
        if self.is_lol_connected:
            async with self.http_session.delete(f'https://{self.base_url}/lol-perks/v1/pages', verify_ssl=False):
                pass

    def get_champion_by_id(self, id: int) -> Champion | None:
        for champion in self.champions:
            if id == champion.id:
                return champion

    def get_champion_by_name(self, name: str) -> Champion | None:
        for champion in self.champions:
            if name == champion.name:
                return champion

    def get_page_rune_champion(self, rune_page: RunePage) -> Champion:
        for word in rune_page.name.split():
            best_match = RatioMatch(None, 0)
            for champion in self.champions:
                match_ratio = jellyfish.jaro_winkler_similarity(flanautils.remove_accents(word.lower()), flanautils.remove_accents(champion.name.lower()))
                if match_ratio >= constants.MIN_RATIO and match_ratio > best_match.ratio:
                    best_match = RatioMatch(champion, match_ratio)

            if best_match.element is not None:
                return best_match.element
        raise NoChampion

    def load_data(self):
        try:
            with open('resources/data.json', 'x') as file:
                file.write('{}')
        except FileExistsError:
            pass

        with open('resources/data.json', 'r+') as file:
            raw_dict = json.load(file)

            self.qt_app.check_box_auto.blockSignals(True)
            try:
                checked = raw_dict['config']['auto']
            except KeyError:
                checked = True
            try:
                list_visible = raw_dict['config']['list_visible']
            except KeyError:
                list_visible = False
            self.qt_app.check_box_auto.setChecked(checked)
            self.qt_app.set_list_rune_pages_visibility(list_visible)
            self.qt_app.check_box_auto.blockSignals(False)

            try:
                rune_pages_data = raw_dict['rune_pages']
            except KeyError:
                rune_pages_data = {}
            return {int(champion_id): [RunePage.from_json(rune_page_json) for rune_page_json in rune_pages] for champion_id, rune_pages in rune_pages_data.items()}

    def on_current_text_changed(self):
        self.current_champion = self.get_champion_by_name(self.qt_app.combo_search.currentText())
        self.set_rune_pages()

    async def run(self):
        lol_versions = await flanautils.get_request(constants.VERSIONS_ENDPOINT)
        champions_data = await flanautils.get_request(constants.CHAMPIONS_BASE_ENDPOINT.format(lol_versions[0]))
        self.champions = [Champion(int(champion_data['key']), champion_data['id']) for champion_data in champions_data['data'].values()]
        self.qt_app.run()
        await asyncio.sleep(0)
        self.qt_app.combo_search.items = [self.get_champion_by_id(champion_id).name for champion_id in self.saved_rune_pages]
        process = await process_utils.return_ux_process_when_available()
        cli_args = process.cmdline()
        auth_key = process_utils.find_auth_key(cli_args)
        port = process_utils.find_port(cli_args)
        self.base_url = f'127.0.0.1:{port}'

        async with aiohttp.ClientSession(auth=aiohttp.BasicAuth('riot', auth_key), headers={'Content-Type': 'application/json', 'Accept': 'application/json'}) as self.http_session:
            async with aiohttp.ClientSession(auth=aiohttp.BasicAuth('riot', auth_key), headers={'Content-Type': 'application/json', 'Accept': 'application/json'}) as ws_session:
                while True:
                    try:
                        ws = await ws_session.ws_connect(f'wss://{self.base_url}', ssl=False)
                        break
                    except aiohttp.ClientConnectorError:
                        await asyncio.sleep(2)

                await ws.send_json([5, 'OnJsonApiEvent'])  # this 5 got from other library I don't know what is
                await ws.receive()
                self.is_lol_connected = True

                while True:
                    msg = await ws.receive()
                    if msg.type == aiohttp.WSMsgType.CLOSED:
                        break
                    msg_data = json.loads(msg.data)[2]
                    uri = msg_data['uri']
                    data = msg_data['data']

                    if uri == '/lol-perks/v1/currentpage' and data['isDeletable']:  # to save rune pages
                        try:
                            self.add_rune_page(
                                RunePage(data['isActive'],
                                         data['name'],
                                         data['order'],
                                         data['primaryStyleId'],
                                         data['subStyleId'],
                                         data['selectedPerkIds'])
                            )
                        except NoChampion:
                            continue
                    elif (
                            self.qt_app.check_box_auto.isChecked()
                            and
                            (
                                    ('/lol-champ-select/v1/grid-champions' in uri and data['selectionStatus']['selectedByMe'] and (not self.current_champion or data['id'] != self.current_champion.id))
                                    or
                                    (uri == '/lol-champ-select/v1/current-champion' and self.current_champion is None)
                            )
                    ):  # set rune pages by champion selected
                        try:
                            champion_id = data['id']
                        except TypeError:
                            champion_id = data
                        self.current_champion = self.get_champion_by_id(champion_id)
                        self.set_rune_pages()

    def save_data(self):
        with open('resources/data.json', 'w') as file:
            rune_pages_data = {champion_id: [rune_page.to_json() for rune_page in rune_pages] for champion_id, rune_pages in self.saved_rune_pages.items()}
            json.dump({
                'rune_pages': rune_pages_data,
                'config': {
                    'auto': self.qt_app.check_box_auto.isChecked(),
                    'list_visible': self.qt_app.list_rune_pages.isVisible()
                }
            }, file)

    def set_rune_pages(self):
        async def set_rune_pages_():
            await self.delete_rune_pages()
            if not self.current_champion:
                self.qt_app.list_rune_pages.clear()
                return
            local_champion = self.current_champion
            selected_rune_pages = self.saved_rune_pages.get(local_champion.id, [])
            combo_index = self.qt_app.combo_search.findText(local_champion.name)
            self.qt_app.combo_search.setCurrentIndex(combo_index)
            self.qt_app.list_rune_pages.items_ = selected_rune_pages
            if self.is_lol_connected:
                for selected_rune_page in selected_rune_pages:
                    if local_champion != self.current_champion:
                        break

                    async with self.http_session.post(f'https://{self.base_url}/lol-perks/v1/pages', data=selected_rune_page.to_json(), verify_ssl=False):
                        pass

        asyncio.create_task(set_rune_pages_())

    def update_runes(self):
        # noinspection PyUnresolvedReferences
        rune_pages = [item.data_ for item in self.qt_app.list_rune_pages.items_]
        if rune_pages:
            self.saved_rune_pages[self.current_champion.id] = rune_pages
            self.set_rune_pages()
        else:
            del self.saved_rune_pages[self.current_champion.id]
            self.qt_app.combo_search.delete_item(self.current_champion.name)
            self.current_champion = None
            self.qt_app.combo_search.setCurrentIndex(-1)
        self.save_data()
