from datetime import date

MONTH_CHOICES = [('', 'Month')] + [(m, f'{m:02d}') for m in range(1, 12+1)]
year = int(date.today().year)
YEAR_CHOICES = [('', 'Year')] + [(y, y) for y in range(year, year + 10)]

AVS_RESPONSES = (
    ('M', 'Matched'),
    ('N', 'Not Matched'),
    ('I', 'Problem with check'),
    ('U', 'Unable to check'),  # not certified etc
    ('P', 'Partial Match')
)
