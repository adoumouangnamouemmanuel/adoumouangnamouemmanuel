"""Refresh repository-owned profile statistics from GitHub's GraphQL API."""
import datetime
import html
import json
import os
from pathlib import Path
import urllib.request

QUERY = '''query($login:String!) {
  user(login:$login) {
    followers { totalCount }
    repositories(first:100,ownerAffiliations:OWNER,privacy:PUBLIC) {
      totalCount nodes { stargazerCount }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}'''


def render(user, updated):
    calendar = user['contributionsCollection']['contributionCalendar']
    repos = user['repositories']
    values = [
        ('PUBLIC REPOSITORIES', repos['totalCount']),
        ('STARS ON LISTED REPOS', sum(r['stargazerCount'] for r in repos['nodes'])),
        ('FOLLOWERS', user['followers']['totalCount']),
        ('CONTRIBUTIONS / YEAR', calendar['totalContributions']),
    ]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="290" viewBox="0 0 1000 290" role="img" aria-labelledby="title desc">',
             '<title id="title">GitHub activity</title>',
             '<desc id="desc">Public repository statistics and the past year contribution calendar. Updated '+html.escape(updated)+'.</desc>',
             '<rect width="1000" height="290" rx="18" fill="#0b1220"/>',
             '<g font-family="Arial,sans-serif">']
    for i, (label, value) in enumerate(values):
        x = 30 + i * 245
        parts.append(f'<text x="{x}" y="48" fill="#60a5fa" font-size="12" letter-spacing="1">{label}</text><text x="{x}" y="89" fill="#f8fafc" font-size="32" font-weight="700">{value:,}</text>')
    colors = {'NONE':'#1e293b','FIRST_QUARTILE':'#1e40af','SECOND_QUARTILE':'#2563eb','THIRD_QUARTILE':'#60a5fa','FOURTH_QUARTILE':'#bfdbfe'}
    for col, week in enumerate(calendar['weeks']):
        for day in week['contributionDays']:
            row = (datetime.date.fromisoformat(day['date']).weekday() + 1) % 7
            x, y = 30 + col * 17.6, 120 + row * 17
            title = html.escape(f"{day['date']}: {day['contributionCount']} contributions")
            parts.append(f'<rect x="{x:.1f}" y="{y}" width="13" height="13" rx="3" fill="{colors[day["contributionLevel"]]}"><title>{title}</title></rect>')
    parts.append(f'<text x="30" y="267" fill="#94a3b8" font-size="11">GitHub-reported activity · Rolling year · Updated {html.escape(updated)} UTC</text></g></svg>')
    return '\n'.join(parts)


def main():
    login = os.environ.get('PROFILE_LOGIN', 'adoumouangnamouemmanuel')
    payload = json.dumps({'query':QUERY,'variables':{'login':login}}).encode()
    request = urllib.request.Request('https://api.github.com/graphql',data=payload,headers={
        'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],
        'Content-Type':'application/json','User-Agent':'profile-stats-refresh'})
    with urllib.request.urlopen(request,timeout=30) as response:
        result = json.load(response)
    if result.get('errors'):
        raise RuntimeError(json.dumps(result['errors']))
    svg = render(result['data']['user'],datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d'))
    target = Path('assets/generated/github-stats.svg')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(svg,encoding='utf-8')


if __name__ == '__main__':
    main()
