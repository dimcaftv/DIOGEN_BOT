from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class Week:
    week: int
    year: int

    @staticmethod
    def weekday_name(d: date) -> str:
        m = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        return m[d.weekday()]

    @classmethod
    def standart_day_format(cls, d: date) -> str:
        return f'{cls.weekday_name(d)} - {d.strftime("%d.%m")}'

    def next(self):
        nw = Week(self.week % 53 + 1, self.year + (self.week == 53))
        if nw[0] == self[0]:
            nw = nw.next()
        return nw

    def prev(self):
        pw = Week((self.week - 2) % 53 + 1, self.year - (self.week == 1))
        if pw[0] == self[0]:
            pw = pw.prev()
        return pw

    def __iter__(self):
        return (self[i] for i in range(1, 8))

    def __getitem__(self, item: int) -> date:
        return datetime.strptime(f'{item % 7}-{self.week}-{self.year}', '%w-%W-%y').date()

    @classmethod
    def today(cls):
        return cls.from_day(date.today())

    @classmethod
    def from_str(cls, s):
        return cls(*map(int, s.split('-')))

    @classmethod
    def from_day(cls, d: date):
        return cls.from_str(d.strftime('%W-%y'))

    def __str__(self):
        return f'{self.week}-{self.year}'
