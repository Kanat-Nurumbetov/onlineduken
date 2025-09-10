from screens import login_screen


def test_od_enter(login, text_finder):
    assert text_finder.present_anywhere("Мои заказы", timeout=10)

