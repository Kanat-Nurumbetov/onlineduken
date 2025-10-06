from screens.main_od_screen import MainOdScreen

def test_od_enter(login, driver):
    od = MainOdScreen(driver)
    assert od.text.find_anywhere("Мои заказы", timeout=10)

