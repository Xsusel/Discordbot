# Discord Bot w Dockerze

Ten projekt dostarcza uproszczonego, solidnego bota Discord, możliwego do wdrożenia za pomocą Dockera. Bot koncentruje się na podstawowych funkcjach, takich jak śledzenie aktywności użytkowników i prosty system ekonomii, przebudowany od podstaw w celu zapewnienia stabilności i łatwości użytkowania.

## Funkcje

-   **Zunifikowany system punktów**: Śledzi dwa rodzaje punktów:
    -   **Punkty Aktywności (AP)**: Zdobywane za wysyłanie wiadomości i aktywność głosową. Używane do tworzenia rankingu aktywności.
    -   **Punkty Hazardu (GP)**: Używane jako waluta do obstawiania i kupowania ról w sklepie.
-   **Prosta ekonomia**: Obstawiaj swoje Punkty Hazardu lub wydawaj je w sklepie z rolami na serwerze.
-   **Skonteneryzowany**: Uruchamia bota w kontenerze, co ułatwia wdrożenie.

## Wymagania wstępne

-   Na twoim systemie musi być zainstalowany [Docker](https://docs.docker.com/get-docker/).

## Konfiguracja i zaproszenie bota

### 1. Utwórz aplikację bota
1.  Przejdź do [Portalu deweloperów Discorda](https://discord.com/developers/applications).
2.  Kliknij **"New Application"**, nadaj jej nazwę i kliknij **"Create"**.
3.  Przejdź do zakładki **"Bot"**.
4.  W sekcji "Privileged Gateway Intents" włącz:
    -   **SERVER MEMBERS INTENT**
    -   **MESSAGE CONTENT INTENT**
5.  Kliknij **"Save Changes"**.

### 2. Zdobądź token bota
-   W zakładce **"Bot"** kliknij **"Reset Token"**, aby uzyskać token bota. **Traktuj go jak hasło i trzymaj w tajemnicy.**

### 3. Zaproś bota na swój serwer
1.  Przejdź do zakładki **"OAuth2"**, a następnie **"URL Generator"**.
2.  W **"SCOPES"** zaznacz pole `bot` i `applications.commands`.
3.  W **"BOT PERMISSIONS"** zaznacz następujące uprawnienia:
    -   `Send Messages`
    -   `Read Message History`
    -   `Embed Links`
    -   `Connect`
    -   `Speak`
    -   `Manage Roles` (dla sklepu z rolami)
4.  Skopiuj wygenerowany adres URL i wklej go w przeglądarce, aby zaprosić bota na swój serwer.

## Konfiguracja projektu

1.  **Sklonuj repozytorium:**
    ```bash
    git clone <adres-repozytorium>
    cd <katalog-repozytorium>
    ```
2.  **Utwórz i skonfiguruj plik `bot.env`:**
    Utwórz plik o nazwie `bot.env` w głównym katalogu projektu z następującą zawartością:
    ```
    # Sekretny token twojego bota z Portalu deweloperów Discorda
    DISCORD_TOKEN=TWÓJ_TOKEN_BOTA_DISCORD
    ```
    Zastąp `TWÓJ_TOKEN_BOTA_DISCORD` swoim rzeczywistym tokenem.

## Uruchamianie bota

Zbuduj i uruchom kontener Dockera za pomocą tej komendy:

```bash
docker build -t discord-bot . && docker run --env-file bot.env -d --name my-discord-bot discord-bot
```

## Komendy bota

Wszystkie komendy są teraz komendami slash (/).

### Komendy użytkownika

-   `/top [period]`: Pokazuje ranking najbardziej aktywnych użytkowników (Punkty Aktywności). Użyj `monthly`, aby zobaczyć ranking z tego miesiąca.
-   `/wallet`: Pokazuje ranking najbogatszych użytkowników (Punkty Hazardu).
-   `/balance [member]`: Sprawdza twoje lub innego użytkownika saldo Punktów Hazardu.
-   `/bet <amount>`: Obstawia określoną ilość twoich Punktów Hazardu.
-   `/shop`: Wyświetla role dostępne do zakupu za Punkty Hazardu.
-   `/buy <item_id>`: Kupuje rolę ze sklepu.

### Komendy administratora

-   `/givepoints <member> <amount>`: Daje użytkownikowi określoną ilość Punktów Hazardu.
-   `/takepoints <member> <amount>`: Zabiera użytkownikowi określoną ilość Punktów Hazardu.
-   `/shopadmin add <role> <price>`: Dodaje rolę do sklepu.
-   `/shopadmin remove <item_id>`: Usuwa rolę ze sklepu na podstawie jej ID.

## Zatrzymywanie bota

Aby zatrzymać i usunąć kontener, uruchom:
```bash
docker stop my-discord-bot && docker rm my-discord-bot
```
