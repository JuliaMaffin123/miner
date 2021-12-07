import sys
import random
from enum import Enum

# Импортируем из PyQt5.QtWidgets классы для создания приложения и виджета
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLineEdit, QLCDNumber
from PyQt5.QtCore import (Qt, pyqtSignal)
from threading import Timer
from datetime import datetime


# Состояние кнопки
class State(Enum):
    CLOSE = 1
    MINE = 2
    FLAG = 3
    OPEN = 4


# Таймер, который будет отсчитывать время партии
class PerpetualTimer:

    def __init__(self, s, f_tick, f_stop):
        # Время в секундах между тиками
        self.time_out = 1
        # Время в секундах до остановки таймера
        self.max_seconds = s
        # Функция срабатывающая на тик таймера
        self.f_tick = f_tick
        # Функция срабатывающая при остановке таймера
        self.f_stop = f_stop
        # Время запуска таймера
        self.now = datetime.now()
        # Всего прошло секунд
        self.total = 0
        # Запускаем таймер
        self.thread = Timer(self.time_out, self.handle_function)

    def handle_function(self):
        # Посчитаем сколько секунд прошло с момента запуска таймера
        cur_time = datetime.now()
        delta = cur_time - self.now
        self.total = delta.total_seconds()
        # Отработаем функцию на тик таймера
        self.f_tick()
        if self.total > self.max_seconds:
            # Отработаем функцию на остановку таймера
            self.f_stop()
        else:
            # Запланируем следующее срабатывание таймера
            self.thread = Timer(self.time_out, self.handle_function)
            self.thread.start()

    def start(self):
        self.thread.start()

    def cancel(self):
        self.thread.cancel()

    def get_total(self):
        return self.total


# Кнопка с дополнительными данными о мине под ней
class MinerButton(QPushButton):
    # Пользовательские сигналы на нажатие кнопок мыши
    leftClick = pyqtSignal()
    rightClick = pyqtSignal()

    def __init__(self, x, y, parent=None):
        # координаты кнопки на поле
        self.x = x
        self.y = y
        # число мин рядом с кнопкой
        self.counter = 0
        # является ли кнопка миной
        self.mine = False
        # Иницируем кнопку
        super(MinerButton, self).__init__(parent)
        # Состояние по умолчанию
        self.set_state(State.CLOSE)

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y

    def get_counter(self):
        return self.counter

    def add_counter(self):
        if not self.mine:
            self.counter += 1
            # DEBUG
            # self.setText(f'{self.counter}')
            # self.setFont(QFont("Courier", 10))

    def set_mine(self, mine):
        self.mine = mine

    def is_mine(self):
        return self.mine

    def clear_state(self):
        self.counter = 0
        self.mine = False
        self.set_state(State.CLOSE)

    def toggle_state(self):
        if self.state == State.CLOSE:
            self.set_state(State.MINE)
        elif self.state == State.MINE:
            self.set_state(State.FLAG)
        elif self.state == State.FLAG:
            self.set_state(State.CLOSE)

    def set_state(self, state):
        self.state = state
        if state == State.MINE:
            self.setText("M")
            self.setStyleSheet('color:black;')
            self.setFont(QFont("Wingdings", 10))
            self.setEnabled(True)
        elif state == State.FLAG:
            self.setText("?")
            self.setStyleSheet('color:green;')
            self.setFont(QFont("Courier", 10))
            self.setEnabled(True)
        elif state == State.CLOSE:
            self.setText("")
            self.setStyleSheet('color:black;')
            self.setFont(QFont("Courier", 10))
            self.setEnabled(True)
        else:
            if self.counter == 0:
                self.setText('')
            else:
                self.setText(f'{self.counter}')
            self.setStyleSheet('color:black;')
            self.setFont(QFont("Courier", 10))
            self.setEnabled(False)

    def get_state(self):
        return self.state

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            print("Left Button Clicked")
            self.leftClick.emit()
        elif event.button() == Qt.RightButton:
            print("Right Button Clicked")
            self.rightClick.emit()


# Унаследуем наш класс от простейшего графического примитива QWidget
class Example(QWidget):

    def __init__(self):
        # Надо не забыть вызвать инициализатор базового класса
        super().__init__()
        # Настройки игры
        self.max_time = 600
        self.game = False
        self.desk = list()
        # В метод initUI() будем выносить всю настройку интерфейса, чтобы не перегружать инициализатор
        self.initUI()

    def initUI(self):
        # Зададим размер и положение нашего виджета,
        self.setGeometry(300, 300, 500, 540)
        self.setMinimumSize(500, 540)
        self.setMaximumSize(500, 540)
        # А также его заголовок
        self.setWindowTitle('Сапёр')
        # Добавляем кнопку запуска
        self.btn_start = QPushButton('Начать', self)
        self.btn_start.resize(100, 40)
        self.btn_start.clicked.connect(self.new_game)
        # Добавляем таймер игры
        self.timer = QLCDNumber(self)
        self.timer.move(400, 0)
        self.timer.resize(100, 40)
        self.timer.display('00:00')
        # Добаволяем инфо поле
        self.info = QLineEdit(self)
        self.info.resize(300, 40)
        self.info.move(100, 0)
        self.info.setReadOnly(True)
        self.info.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.info.setText('Сапёр ошибается только раз!')
        # Заполняем поле
        # Создаем поле кнопок
        for i in range(10):
            row_desk = list()
            for j in range(10):
                # Создаем кнопку
                btn = MinerButton(i, j, self)
                btn.resize(51, 51)
                btn.move(i * 50, j * 50 + 40)
                btn.leftClick.connect(self.open_cell)
                btn.rightClick.connect(self.flag_cell)
                row_desk.append(btn)
            self.desk.append(row_desk)

    # Запускает новую игру
    def new_game(self):
        print("NEW GAME")
        # Заполняем поле минами
        self.fill_mine()
        # Настраиваем внешний вид формы
        self.info.setText('Будь внимателен сапёр!')
        self.timer.setStyleSheet('background:green;color:white;')
        # Запускаем таймер
        self.game_timer = PerpetualTimer(self.max_time, self.timer_show, self.game_over)
        self.game_timer.start()
        # Разрешаем делать ходы
        self.game = True

    # Завершение игры по таймеру
    def game_over(self):
        print("GAME OVER")
        self.info.setText('Время вышло! GAME OVER...')
        self.timer.setStyleSheet('background:red;color:white;')
        self.game = False
        for i in range(10):
            for j in range(10):
                btn = self.desk[i][j]
                btn.setEnabled(False)

    # Завершение игры при подрыве
    def game_over(self, btn):
        btn.setText("®")
        btn.setStyleSheet('color:red;')
        btn.setFont(QFont("Wingdings", 10))
        self.game = False
        self.info.setText('БА-БАХ! GAME OVER...')
        self.timer.setStyleSheet('background:red;color:white;')
        self.game_timer.cancel()

    # Завершение игры при победе
    def game_win(self):
        self.game = False
        self.info.setText('ПОБЕДА! Найдены все мины.')
        self.game_timer.cancel()

    # Обновление времени игры
    def timer_show(self):
        total = self.game_timer.get_total()
        m = int(total // 60)
        s = int(total - m * 60)
        m_str = str(m).rjust(2, '0')
        s_str = str(s).rjust(2, '0')
        self.timer.display(f'{m_str}:{s_str}')
        print(f'TICK GAME: {m}:{s} total={total}')

    # Заполняет поле минами в начале игры
    def fill_mine(self):
        # Очищаем состояние всех кнопок
        for row in self.desk:
            for el in row:
                el.clear_state()
        # Расставляем на поле мины
        for i in range(10):
            for j in range(10):
                btn = self.desk[i][j]
                # Генерируем случайное число в диапазоне 1..100
                cell = random.randint(1, 100)
                if cell > 80:
                    # Ставим мину для 20% заполнения
                    btn.set_mine(True)
                    self.up_counters(i, j)
                    # DEBUG:
                    # btn.setText(">")
                    # btn.setFont(QFont("Wingdings", 10))

    # Вскрывает клетку
    def open_cell(self):
        if self.game:
            btn = self.sender()
            # Проверим нет ли мины под кнопкой?
            if btn.is_mine():
                # Останавливаем игру
                self.game_over(btn)
                return
            # Если кнопка без флага, откроем ее
            if btn.get_state() == State.CLOSE:
                self.check_cell(btn.get_x(), btn.get_y())
                print("OPEN:", btn.is_mine(), btn.get_x(), btn.get_y())

    # Выставляет флаг
    def flag_cell(self):
        btn = self.sender()
        if self.game:
            print("FLAG:", btn.is_mine(), btn.get_x(), btn.get_y())
            btn.toggle_state()
            if self.is_win():
                self.game_win()

    # Подсчитывает число контактов с минами по всем клеткам
    def up_counters(self, i, j):
        # Левый столбец
        if j - 1 >= 0:
            # Строка выше
            if i - 1 >= 0:
                self.desk[i - 1][j - 1].add_counter()
            # Текущая строка
            self.desk[i][j - 1].add_counter()
            # Строка ниже
            if i + 1 < 10:
                self.desk[i + 1][j - 1].add_counter()
        # Текущий столбец
        # Строка выше
        if i - 1 >= 0:
            self.desk[i - 1][j].add_counter()
        # Строка ниже
        if i + 1 < 10:
            self.desk[i + 1][j].add_counter()
        # Правый столбец
        if j + 1 < 10:
            # Строка выше
            if i - 1 >= 0:
                self.desk[i - 1][j + 1].add_counter()
            # Текущая строка
            self.desk[i][j + 1].add_counter()
            # Строка ниже
            if i + 1 < 10:
                self.desk[i + 1][j + 1].add_counter()

    # Вскрывает соседние клетки, если попали в пустое поле
    def check_cell(self, x, y):
        if x < 0 or x >= 10 or y < 0 or y >= 10:
            # Игнорируем выход за поле
            return
        # Рекурсивно обходим ячейки и пытаемся их открывать
        btn = self.desk[x][y]
        state = btn.get_state()
        if state == State.FLAG or state == State.MINE or state == State.OPEN:
            # Игнорируем помеченные и открытые клетки
            return
        btn.set_state(State.OPEN)
        # Если кнопка не граничит с минами, вскрываем соседние
        if btn.get_counter() == 0:
            self.check_cell(x - 1, y - 1)
            self.check_cell(x, y - 1)
            self.check_cell(x + 1, y - 1)
            self.check_cell(x - 1, y)
            self.check_cell(x + 1, y)
            self.check_cell(x - 1, y + 1)
            self.check_cell(x, y + 1)
            self.check_cell(x + 1, y + 1)

    # Проверка на выигрыш: все мины должны быть помечены
    def is_win(self):
        for row in self.desk:
            for btn in row:
                if btn.is_mine():
                    if btn.get_state() != State.MINE:
                        # DEBUG:
                        # print(f'МИНА на: {btn.get_x()}..{btn.get_y()}')
                        return False
                else:
                    continue
        return True

    # Закрывает приложение по ESC
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()

    # Остановка таймера при закрытии окна
    def closeEvent(self, event):
        self.game_timer.cancel()
        event.accept()


if __name__ == '__main__':
    # Создадим класс приложения PyQT
    app = QApplication(sys.argv)
    app.setStyleSheet('''
        QLineEdit {
            border: 1px solid gray;
            padding: 5px;
        }
        QPushButton {
            border: 1px solid gray;
        }
        QLCDNumber {
            color: black;
            border: 1px solid gray;
        }
        MinerButton {
            background: white;
            font-size: 12pt;
            font-weight: bold;
        }
        MinerButton::disabled {
            background: #CCCCCC;
        }
    ''')
    # А теперь создадим и покажем пользователю экземпляр
    # нашего виджета класса Example
    ex = Example()
    ex.show()
    # Будем ждать, пока пользователь не завершил исполнение QApplication,
    # а потом завершим и нашу программу
    sys.exit(app.exec())

