import re
import csv
import datetime
import pytz

g_summary_re = "([\w ]+) [vV]s? ([\w ]+).*"

def parse_events(file_name, debug=False):
    with open(file_name) as file:
        events = []
        event = None
        for line in file.readlines():
            line = line.strip()
            if not len(line):
               continue
            if debug:
                print(line)
            if "BEGIN:VEVENT" in line:
               event = {}
            elif event is None:
              continue
            elif "END:VEVENT" in line:
                if "SUMMARY" in event:
                    events.append(event)
                event = None
            else:
              try:
                  key, value = line.split(':', 1)
                  event[key] = value
              except ValueError:
                  continue
        return events


def matches_to_csv(matches, file_name):
    header = ["match_id", "home_team", "away_team", "kick_off", "home_team_winner_of", "away_team_winner_of"]

    if not len(matches):
        return

    with open(file_name, 'w+') as file:
        writer = csv.DictWriter(file, fieldnames=header, )
        writer.writeheader()

        for row in matches:
            writer.writerow(row)


def events_to_matches(events, summary_re=g_summary_re, team_list=None):
    rows = []
    curr_id = 1
    for event in events:
        s = re.search(summary_re, event["SUMMARY"])
        if s is None:
            continue
        home = s.group(1).strip()
        away = s.group(2).strip()
        if team_list is not None:
            if home not in team_list:
                continue
            if away not in team_list:
                continue

        row = {
           'match_id': curr_id,
           'home_team': home,
           'away_team': away,
           'kick_off': datetime.datetime.strptime(
               event["DTSTART"],
               "%Y%m%dT%H%M%SZ"
               ).astimezone(pytz.utc)
        }
        rows.append(row)
        curr_id += 1

    return rows


def events_to_csv(events, file_name, summary_re=g_summary_re):
    rows = events_to_matches(events, summary_re)
    matches_to_csv(rows, file_name)


def teams_to_csv(teams, file_name, country=False):
    header = ["name", "code"]
    if country:
        import pycountry

    if len(teams):
        with open(file_name, 'w+') as file:
            writer = csv.DictWriter(file, fieldnames=header)
            writer.writeheader()
            for team in teams:
                row = {"name": team}
                if country:
                    c = pycountry.countries.get(name=team)
                    if c is not None:
                        row["code"] = c.alpha_3
                writer.writerow(row)


def matches_to_teams(matches):
    teams = []

    for m in matches:
        if m['home_team'] not in teams:
            teams.append(m['home_team'])
        if m['away_team'] not in teams:
            teams.append(m['away_team'])

    return teams


if __name__ == "__main__" :
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("in_filename")
    parser.add_argument("out_filename")
    parser.add_argument("-v", "--debug",
                        default=False,
                        action="store_true")
    parser.add_argument("--teams",
                        default=False,
                        action="store_true",
                        help="Output a team,code csv file from all the matches")
    parser.add_argument("--regx",
                        default=g_summary_re,
                        help="RegEx to used on Event summary to get team details, default '%s'" % g_summary_re)
    parser.add_argument("--country",
                        default=False,
                        action="store_true",
                        help="Use pycountry to add code to teams file")
    parser.add_argument("--team_list",
                        help="Only include matches when both teams are in this list")

    args = parser.parse_args()

    if args.debug:
        print(args.regx)
    events = parse_events(args.in_filename, args.debug)

    team_list = None
    if args.team_list:
        team_list = args.team_list.split(',')

    matches = events_to_matches(events, args.regx, team_list)
    if args.teams:
        teams = matches_to_teams(matches)
        teams_to_csv(teams, args.out_filename, args.country)
    else:
        matches_to_csv(matches, args.out_filename)
