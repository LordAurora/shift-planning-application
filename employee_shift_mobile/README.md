# ShiftMaster AI — Employee Mobile App

The Flutter client employees use to view their shifts, manage leave and set shift preferences. It is built offline-first: data is cached in SQLite, and changes are queued and synced when the device is back online.

## Features

- Secure login (JWT stored in `flutter_secure_storage`)
- Home overview and weekly shift calendar
- Leave requests: create a request and track its status
- Shift preferences: preferred days and shift types
- Notifications (Firebase Cloud Messaging + local notifications)
- Profile management
- Background sync every 5 minutes, with retry and server-wins conflict resolution

## Stack

Flutter · Dart · Provider · Dio · go_router · sqflite · shared_preferences · connectivity_plus · firebase_messaging · flutter_animate

## Run

```bash
flutter pub get
flutter run
```

The app connects to the ShiftMaster AI backend. On an Android emulator, the host machine's backend is reachable at `http://10.0.2.2:8000`.

See the [root README](../README.md) for the full system setup.
