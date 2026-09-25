# Hackaton 2026

A phone-friendly Möbius app for joining a hackathon, exploring challenges,
and sharing findings with other participants. Cream surfaces, cobalt type,
and coral, yellow and mint illustrations give it a science-festival theme.

## Event programme

Organized by ANNT, 28 September–9 October 2026. Six real briefs: Agent
marketplace, Game studio, Multiplayer & shared worlds, Immersive gallery,
Private pro desk, and Möbius speaks. The first three are flagship bounties
(1,400 BAM each); the remaining three are open briefs (700 BAM each).

`programme.json` owns the briefs, dates, organizer information, and rules used
by both the service and the UI. Organizer description source:
https://annt.ba/o-nama/ . The welcome links to https://annt.ba/ .

Rewards show mystery top-three podiums for apps and games, plus the platform
pool, Community MVP, and best meme. No overall prize total or estimated
participant count is displayed. Actual per-challenge membership counts remain.
Jury decisions, scoring and payouts are not automated. Joining a challenge is
participation, not a project submission or a prize award. Jury names, exact
submission cut-offs and contributor split method remain unannounced.

The organizer approved removing the original sample challenges and their
associated discussions/memberships on 25 September 2026. New briefs have new
stable IDs and never inherit sample activity. Event registrations remain.

## Participate

1. Install in your own Möbius and connect a Möbius identity with an @handle.
2. New installations connect to the shared event at
   `mobius-production-56cd.up.railway.app` automatically. An explicitly saved
   alternate host stays selected and is visibly marked as a separate event;
   choose **Use shared event** to switch. Old comments and memberships stay
   on the original installation and are not moved or deleted.
3. Join the event, read the rules, then open and join a challenge.
4. Share findings, links, PNG/JPEG/WebP images (up to 1 MB), and threaded replies.
   You can edit or delete your own findings and replies. Other people's replies
   remain when their parent is deleted.

An internet connection is required. Each participant needs a publicly reachable
Möbius installation registered to their identity for cross-host participation.

## Privacy and permissions

The app uses Möbius identity permission to verify participants. The organizer's
installation holds event memberships and discussions in app-scoped SQLite.
Participant lists, findings and images require challenge membership. Public
service routes exchange short-lived, request-bound identity proofs; owner
credentials are never sent to peers. Outbound peer requests use DNS-pinned
public HTTPS, no redirects, and bounded responses.

Publishing this package does not publish the organizer's event database,
findings, attachments, host preferences, or credentials. Store screenshots omit
account labels, host settings and participation counts. No participant posts
are included in the listing artwork.

## Implementation

- `index.jsx`: onboarding, event connection and navigation.
- `Programme.jsx` / `programme.json`: shared programme content and welcome/rules views.
- `Challenge.jsx`: findings, images and threaded replies.
- `Rewards.jsx`: mystery podiums with anchored shadows and floating pals.
- `theme.js` / `ChallengeArt.jsx`: responsive styling and illustrations.
- `service.py` / `domain.py`: identity checks, authorization and transactions.
- `peer_transport.py`, `net_utils.py`, `dns_resolver.py`: reused Möbius
  federation transport helpers.

Reduced-motion preferences disable animation automatically. There are no
manual animation-stop controls. Post-success feedback runs only after a saved
finding is present in the refreshed feed; failed submissions retain the draft.

## Tests

From the package directory in a Möbius Python environment:

```sh
python -m unittest test_hackaton.py test_shared_event.py
node --test test_refresh.mjs
```

Tests use temporary databases and fake identities, not a live event. They cover
onboarding, membership gates, attachments, replay safety, author-only edits and
deletes, reply preservation, pagination and federation proof rejection.

Views refresh every 15 seconds while visible and online, and on focus or
reconnection. Expanded replies refresh too; drafts and loaded older pages
remain open. A failed refresh keeps the last view and displays a stale-data
warning. This is periodic refresh, not instantaneous live delivery.
