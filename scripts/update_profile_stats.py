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
        ('Public repositories', repos['totalCount']),
        ('Stars on listed repos', sum(r['stargazerCount'] for r in repos['nodes'])),
        ('Followers', user['followers']['totalCount']),
        ('Contributions / year', calendar['totalContributions']),
    ]
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="467" height="195" viewBox="0 0 467 195" role="img" aria-labelledby="title desc">',
             '<title id="title">GitHub statistics</title>',
             '<desc id="desc">Public repository statistics. Updated '+html.escape(updated)+'.</desc>',
             '<rect width="467" height="195" rx="12" fill="#0b1220"/>',
             '<g font-family="Arial,sans-serif">',
             '<text x="24" y="30" fill="#60a5fa" font-size="18" font-weight="700">GitHub statistics</text>']
    for i, (label, value) in enumerate(values):
        x, y = 24 + (i % 2) * 224, 63 + (i // 2) * 57
        parts.append(f'<text x="{x}" y="{y}" fill="#cbd5e1" font-size="12">{label}</text><text x="{x}" y="{y+27}" fill="#f8fafc" font-size="23" font-weight="700">{value:,}</text>')
    parts.append(f'<text x="24" y="183" fill="#94a3b8" font-size="10">GitHub-reported activity · {html.escape(updated)} UTC</text></g></svg>')
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
