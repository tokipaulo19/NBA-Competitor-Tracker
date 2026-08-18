# NBA Competitor Tracker

Automated competitor intelligence and social media tracking system for Natural Bodybuilding Australia.

## Current Metrics

The system is being designed to track:

- Instagram followers
- Published content
- Follower growth
- Posting growth
- Posting frequency

## Historical Data

Historical manually collected data is stored in:

data/historical.csv

Raw imported data is stored in:

data/historical_raw.csv

## Account Aliases

Historical Instagram handles that have changed are maintained in:

config/aliases.csv

Example:

icntas -> icn_tasmania

## Competitors

The master tracking list is stored in:

config/competitors.csv

## Automation

Future versions will automatically collect competitor statistics every Monday.

The system is designed to run independently of ChatGPT.
