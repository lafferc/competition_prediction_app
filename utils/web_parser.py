import urllib2
import csv
import datetime
import itertools
from bs4 import BeautifulSoup

match_by_str = {}
match_by_id = {}

def get_match(team_str):
    try:
        return match_by_str[team_str]
    except KeyError:
        print("failed to find %s" % team_str)


def add_match(match):
    teams = []
    if match['home_team'] != "TBD":
        teams.append(match['home_team'])
    else:
        m = match_by_id[match["home_team_winner_of"]]
        if m["home_team"] != "TBD" and m["away_team"] != "TBD":
            teams.append(m["home_team"])
            teams.append(m["away_team"])

    if match['away_team'] != "TBD":
        teams.append(match['away_team'])
    else:
        m = match_by_id[match["away_team_winner_of"]]
        if m["home_team"] != "TBD" and m["away_team"] != "TBD":
            teams.append(m["home_team"])
            teams.append(m["away_team"])

    match_by_id[match["match_id"]] = match

    for perm in itertools.permutations(teams):
        match_by_str[" / ".join(perm)] = match


def parse_matches(soup, rows, comps, curr_id=1, tz_delta=None, debug=False):
    for match_li in soup.find_all("li"):
        if "football" not in match_li["class"]:
            if debug:
                print("skipping li, class:%s" % match_li["class"])
            continue
        h3_text = match_li.parent.find_previous_sibling('h3').text
        for name in comps:
            if name in h3_text:
                break
        else:
            if debug:
                print("skipping li, none of the following %r are in previous h3: %s" % (comps, h3_text))
            continue

        row = {
            'match_id': curr_id,
        }
        date = match_li["data-date"]
        if match_li.a is None:
            p_span = match_li.span
        else:
            p_span = match_li.a.span

        for span in p_span.find_all("span"):
            if "team-home" in span["class"]:
                team = span.text.strip()
                if "/" in team and get_match(team):
                    row['home_team'] = "TBD"
                    row['home_team_winner_of'] = get_match(team)["match_id"]
                else:
                    row['home_team'] = team
            elif "team-away" in span["class"]:
                team = span.text.strip()
                if "/" in team and get_match(team):
                    row['away_team'] = "TBD"
                    row['away_team_winner_of'] = get_match(team)["match_id"]
                else:
                    row['away_team'] = team
            elif "score" in span["class"]:
                time = span.text.strip()
                if ":" not in time:
                    time = "12:00"
                if tz_delta is not None:
                    row['kick_off'] = datetime.datetime.strptime(' '.join([date, time]), "%Y-%m-%d %H:%M") + tz_delta
                else:
                    row['kick_off'] = datetime.datetime.strptime(' '.join([date, time]), "%Y-%m-%d %H:%M")

        if debug:
            print("Adding match %r" % row)
        add_match(row)
        rows.append(row)
        curr_id += 1
    return curr_id


if __name__ == "__main__" :
    import argparse
    from calendar_parser import matches_to_csv
    from dateutil.relativedelta import relativedelta

    parser = argparse.ArgumentParser()
    # parser.add_argument("in_url")
    parser.add_argument("out_filename")
    parser.add_argument("-v", "--debug",
                        default=False,
                        action="store_true")
    parser.add_argument("--start_id",
                        type=int,
                        default=1)
    # parser.add_argument("--teams",
    #                     default=False,
    #                     action="store_true")
    parser.add_argument("--tz_delta",
                        type=int,
                        default=0)
    parser.add_argument("--date",
                        help='date to search from e.g. 1-1-2020, default today',
                        type=str)
    parser.add_argument("-m", "--months",
                        type=int,
                        default=1,
                        help='number of months from data to process. Default 1')
    parser.add_argument("--comps",
                        nargs="+",
                        default=["Senior", "Roinn 1", "Roinn 2"],
                        help='list of competition names to check for. Default "Senior" "Roinn 1" "Roinn 2"')

    args = parser.parse_args()

    tz_diff = datetime.timedelta(hours=args.tz_delta)
    next_id = args.start_id;
    if args.date is None:
        start_date = datetime.datetime.now().date()
    else:
        start_date = datetime.datetime.strptime(args.date, '%d-%m-%Y').date()

    url = "https://www.gaa.ie/fixtures-results/library/matches/1/0/0/%s/monthly/_matches-by-date"

    matches = []

    for i in range(args.months):
        date = start_date + relativedelta(months=i)
        if i:
            date = date.replace(day=1)

        if args.debug:
            print("loading page " + url % date)

        page = urllib2.urlopen(url % date)
        soup = BeautifulSoup(page, features="html.parser")

        next_id = parse_matches(soup, matches, args.comps, next_id, tz_diff, debug=args.debug)

    matches_to_csv(matches, args.out_filename)
