import json
from collections import defaultdict
import datetime

groups = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0)))

IN = "umrti.json"
IN_JAB = "ockovani.json"
OUT = "chart.html"

DAY = datetime.timedelta(days=1)


def parse_incident(raw):
    return {
        "date": datetime.date.fromisoformat(raw["datum"]),
        "age": raw["vek"],
        "sex": raw["pohlavi"],
    }


def parse_jab(raw):
    return {
        "date": datetime.date.fromisoformat(raw["datum"]),
        "age_group": raw["vekova_skupina"],
        "first_count": raw["prvnich_davek"],
        "second_count": raw["druhych_davek"],
    }


class Line:
    DASHED = False
    DOTTED = 'dotted'

    def __init__(self, label, filter=None, color='', enabled=True, style=None):
        self.label = label
        self.filter = filter if filter else lambda x: x
        self.color = color
        self.enabled = enabled
        self._points = defaultdict(lambda: 0)
        self.style = style

    def render(self):
        return f"""
            {{
                data: [{", ".join(map(str, self._points.values()))} ],
                borderColor: '{self.color}',
                fill: false,
                label: '{self.label}',
                hidden: {'false' if self.enabled else 'true'},
                yAxisID: '{self.Y_AXIS_LABEL}',
                {"borderDash: [10, 10]," if self.DASHED else ''}
                showLine: {'false' if self.style == self.DOTTED else 'true'},

            }},
        """


class LineDeaths(Line):
    Y_AXIS_LABEL = 'y-axis-deaths'

    def __init__(self, days=1, **kwargs):
        self.days = days
        super().__init__(**kwargs)

    @staticmethod
    def age_filter(start, end):
        def f(i):
            return start <= i['age'] < end

        return f

    def calc(self, data, x):
        for day in x:
            if day not in data:
                continue
            value = 0
            for x in range(self.days):
                if day - x * DAY in data:
                    value += len(list(filter(self.filter, data[day - x * DAY])))
            self._points[day] = value / self.days


class LineJabs(Line):
    Y_AXIS_LABEL = 'y-axis-jabs'
    DASHED = True

    AGE_GROUPS = {
        "0": "0-17",
        "18": "18-24",
        "25": "25-29",
        "30": "30-34",
        "35": "35-39",
        "40": "40-44",
        "45": "45-49",
        "50": "50-54",
        "55": "55-59",
        "60": "60-64",
        "65": "65-69",
        "70": "70-74",
        "75": "75-79",
        "80": "80+",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def age_filter(cls, *groups):
        def f(i):
            return i['age_group'] in groups

        return f

    def calc(self, data, x):
        total = 0
        for day in x:
            total += sum([i['first_count'] for i in filter(self.filter, data[day])])
            self._points[day] = total


class Graph:
    COLORS = [
        '#e41a1c',
        '#377eb8',
        '#4daf4a',
        '#984ea3',
        '#ff7f00',
        '#ffff33',
        '#a65628',
        '#f781bf',
    ]

    def __init__(self, lines):
        self.lines = lines

    def load(self):
        deaths_data = defaultdict(list)
        jabs_data = defaultdict(list)
        with open(IN) as fp:
            for incident_raw in json.load(fp)["data"]:
                incident = parse_incident(incident_raw)
                date = incident['date']
                if date > datetime.date(2020, 9, 1):
                    deaths_data[date].append(incident)
        with open(IN_JAB) as fp:
            for jab_raw in json.load(fp)["data"]:
                jab = parse_jab(jab_raw)
                jabs_data[jab['date']].append(jab)
        self.deaths_data = deaths_data
        self.jabs_data = jabs_data
        self.x = sorted(set(deaths_data.keys()) | set(jabs_data.keys()))
        self.calc()

    def calc(self):
        for l in self.lines:
            if isinstance(l, LineDeaths):
                l.calc(self.deaths_data, self.x)
            elif isinstance(l, LineJabs):
                l.calc(self.jabs_data, self.x)

    def render(self):
        return (
            """
            <script>
            var color = Chart.helpers.color;

            var data = {
                labels: ["""
            + ", ".join([f"'{d.year}-{d.month}-{d.day}'" for d in self.x])
            + """],
                datasets: ["""
            + "\n".join(l.render() for l in self.lines)
            + """
                ]
            }
            </script>
        """
        )


graph = Graph(
    lines=[
        LineJabs(
            label='💉 TOTAL',
            color=Graph.COLORS[6],
            enabled=False,
        ),
        LineJabs(
            label='💉 80+',
            filter=LineJabs.age_filter(LineJabs.AGE_GROUPS['80']),
            color=Graph.COLORS[0],
            enabled=True,
        ),
        LineJabs(
            label='💉 70+',
            filter=LineJabs.age_filter(LineJabs.AGE_GROUPS['70'], LineJabs.AGE_GROUPS['75']),
            color=Graph.COLORS[1],
            enabled=True,
        ),
        LineJabs(
            label='💉 60+',
            filter=LineJabs.age_filter(LineJabs.AGE_GROUPS['60'], LineJabs.AGE_GROUPS['65']),
            color=Graph.COLORS[2],
            enabled=True,
        ),
        LineJabs(
            label='💉 50+',
            filter=LineJabs.age_filter(LineJabs.AGE_GROUPS['50'], LineJabs.AGE_GROUPS['55']),
            color=Graph.COLORS[3],
            enabled=True,
        ),
        LineJabs(
            label='💉 40+',
            filter=LineJabs.age_filter(LineJabs.AGE_GROUPS['40'], LineJabs.AGE_GROUPS['45']),
            color=Graph.COLORS[4],
            enabled=True,
        ),
        LineJabs(
            label='💉 40-',
            filter=LineJabs.age_filter(
                LineJabs.AGE_GROUPS['0'],
                LineJabs.AGE_GROUPS['18'],
                LineJabs.AGE_GROUPS['25'],
                LineJabs.AGE_GROUPS['30'],
                LineJabs.AGE_GROUPS['35'],
            ),
            color=Graph.COLORS[5],
            enabled=True,
        ),
        LineDeaths(
            label='✖ 80+ [per day]',
            filter=lambda i: 80 <= i['age'],
            color=Graph.COLORS[0],
            enabled=False,
            style=Line.DOTTED,
        ),
        LineDeaths(
            label='✖ 80+ [7 days avg]',
            filter=LineDeaths.age_filter(80, 1000),
            days=7,
            color=Graph.COLORS[0],
        ),
        LineDeaths(
            label='✖ 70+ [per day]',
            filter=LineDeaths.age_filter(70, 80),
            color=Graph.COLORS[1],
            enabled=False,
            style=Line.DOTTED,
        ),
        LineDeaths(
            label='✖ 70+ [7 days avg]',
            filter=LineDeaths.age_filter(70, 80),
            days=7,
            color=Graph.COLORS[1],
        ),
        LineDeaths(
            label='✖ 60+ [per day]',
            filter=LineDeaths.age_filter(60, 70),
            days=1,
            color=Graph.COLORS[2],
            enabled=False,
            style=Line.DOTTED,
        ),
        LineDeaths(
            label='✖ 60+ [7 days avg]',
            filter=LineDeaths.age_filter(60, 70),
            days=7,
            color=Graph.COLORS[2],
        ),
        LineDeaths(
            label='✖ 50+ [per day]',
            filter=LineDeaths.age_filter(50, 60),
            days=1,
            color=Graph.COLORS[3],
            enabled=False,
            style=Line.DOTTED,
        ),
        LineDeaths(
            label='✖ 50+ [7 days avg]',
            filter=LineDeaths.age_filter(50, 60),
            days=7,
            color=Graph.COLORS[3],
        ),
        LineDeaths(
            label='✖ 40+ [per day]',
            filter=LineDeaths.age_filter(40, 50),
            days=1,
            color=Graph.COLORS[4],
            enabled=False,
            style=Line.DOTTED,
        ),
        LineDeaths(
            label='✖ 40+ [7 days avg]',
            filter=LineDeaths.age_filter(40, 50),
            days=7,
            color=Graph.COLORS[4],
        ),
        LineDeaths(
            label='✖ 40- [per day]',
            filter=LineDeaths.age_filter(0, 40),
            days=1,
            color=Graph.COLORS[5],
            enabled=False,
            style=Line.DOTTED,
        ),
        LineDeaths(
            label='✖ 40- [7 days avg]',
            filter=LineDeaths.age_filter(0, 40),
            days=7,
            color=Graph.COLORS[5],
        ),
        LineDeaths(
            label='✖ Total [per day]',
            days=1,
            color=Graph.COLORS[6],
            enabled=False,
            style=Line.DOTTED,
        ),
        LineDeaths(
            label='✖ Total [7 days avg]',
            days=7,
            color=Graph.COLORS[6],
            enabled=False,
        ),
    ],
)

graph.load()


TEMPLATE = f"""
<html>
<body>

<script src="Chart.bundle.min.js"></script>

<canvas id="myChart" width="400" height="200"></canvas>
{graph.render()}
<script src="main.js"></script>
</body>
</html>
"""

with open(OUT, 'w') as fp:
    fp.write(TEMPLATE)
