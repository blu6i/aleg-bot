from aiogram.fsm.state import StatesGroup, State


class UpdInfoAlliance(StatesGroup):
    upd_alliances_list = State()
    upd_alliances_menu = State()
    entering_rename = State()
    confirm_rename = State()
    edit_members = State()
    transfer_master = State()
    link_chat = State()
    unlink_chat = State()
    delete_alliance = State()