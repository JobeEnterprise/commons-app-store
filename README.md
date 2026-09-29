## Commons App Store

A Community App Store for umbrelOS. Add apps by creating a new folder with an `umbrel-app.yml` and `docker-compose.yml`.

## How to use:

1. The app store ID is `commons`. Every app ID must start with this prefix (e.g. `commons-my-app`).
2. Create a new folder named after your app ID (e.g. `commons-my-app/`).
3. Add `umbrel-app.yml` with your app's metadata (name, description, icon, etc.).
4. Add `docker-compose.yml` with your app's Docker services.
5. Commit and push. Your app will appear in the Commons App Store on umbrelOS.

To add this app store to umbrelOS, go to the App Store settings and enter:
`https://github.com/JobeEnterprise/commons-app-store`
