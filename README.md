# Discord Bot z panelem internetowym w Dockerze

Ten projekt dostarcza uproszczonego, solidnego bota Discord z panelem internetowym, możliwego do wdrożenia za pomocą Dockera. Bot koncentruje się na podstawowych funkcjach, takich jak śledzenie aktywności użytkowników i prosty system ekonomii, przebudowany od podstaw w celu zapewnienia stabilności i łatwości użytkowania.

## Funkcje

-   **Zunifikowany system punktów**: Śledzi dwa rodzaje punktów:
    -   **Punkty Aktywności (AP)**: Zdobywane za wysyłanie wiadomości i aktywność głosową. Używane do tworzenia rankingu aktywności.
    -   **Punkty Hazardu (GP)**: Używane jako waluta do obstawiania i kupowania ról w sklepie.
-   **Codzienne liczenie członków**: Codziennie zapisuje liczbę członków serwera.
-   **Panel internetowy**: Strona internetowa do wizualizacji statystyk serwera, zawierająca wykres liczby członków i ranking najbardziej aktywnych użytkowników.
-   **Prosta ekonomia**: Obstawiaj swoje Punkty Hazardu lub wydawaj je w sklepie z rolami na serwerze.
-   **Skonteneryzowany**: Uruchamia zarówno bota, jak i serwer internetowy w jednym kontenerze, co ułatwia wdrożenie.

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
2.  W **"SCOPES"** zaznacz pole `bot`.
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
docker build -t discord-bot . && docker run --env-file bot.env -d -p 8080:8080 --name my-discord-bot discord-bot
```

-   `docker build -t discord-bot .`: Buduje obraz Dockera.
-   `docker run ...`: Uruchamia kontener.
    -   `--env-file bot.env`: Ładuje twój sekretny token.
    -   `-d`: Uruchamia w trybie odłączonym.
    -   `-p 8080:8080`: Mapuje port 8080 kontenera na port 8080 twojego hosta.
    -   `--name my-discord-bot`: Nadaje kontenerowi wygodną nazwę.

## Komendy bota

### Komendy użytkownika

-   `$top [monthly]`: Pokazuje ranking najbardziej aktywnych użytkowników (Punkty Aktywności). Użyj `monthly`, aby zobaczyć ranking z tego miesiąca.
-   `$wallet`: Pokazuje ranking najbogatszych użytkowników (Punkty Hazardu).
-   `$balance [@użytkownik]`: Sprawdza twoje lub innego użytkownika saldo Punktów Hazardu.
-   `$bet <kwota>`: Obstawia określoną ilość twoich Punktów Hazardu.
-   `$shop`: Wyświetla role dostępne do zakupu za Punkty Hazardu.
-   `$buy <id_przedmiotu>`: Kupuje rolę ze sklepu.
-   `$dashboard`: Udostępnia link do panelu internetowego dla serwera.

### Komendy administratora

-   `$givepoints <@użytkownik> <kwota>`: Daje użytkownikowi określoną ilość Punktów Hazardu.
-   `$takepoints <@użytkownik> <kwota>`: Zabiera użytkownikowi określoną ilość Punktów Hazardu.
-   `$shopadmin add <@rola> <cena>`: Dodaje rolę do sklepu.
-   `$shopadmin remove <id_przedmiotu>`: Usuwa rolę ze sklepu na podstawie jej ID.

## Panel internetowy

Dostęp do panelu internetowego można uzyskać za pomocą komendy `$dashboard` na swoim serwerze. Panel wyświetla:
-   Wykres liczby członków serwera w czasie.
-   Ranking 10 najbardziej aktywnych użytkowników na podstawie ich Punktów Aktywności.

## Zatrzymywanie bota

Aby zatrzymać i usunąć kontener, uruchom:
```bash
docker stop my-discord-bot && docker rm my-discord-bot
```
