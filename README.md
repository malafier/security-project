# security-project

Prosta aplikację do ewidencji pożyczek. -- Jest grupa użytkowników, którzy chcą pożyczać pomiędzy sobą dowolne kwoty pieniędzy. Chcą zapisywać, kto komu i ile do kiedy pożyczył pieniędzy. Zakładamy, że pożyczający jest dodaje wpis, pożyczkobiorca potwierdza go i ma tylko jego podgląd, a wszyscy pozostali widzą tylko sumaryczne zadłużenie każdej osoby i czy są długi po terminie spłaty.

## Zakres wymagań

- ✓ **(niezbędne)** restrykcyjna walidacja danych pochodzących z formularza login-hasło,
- ✓ **(niezbędne)** przechowywanie hasła chronione funkcją hash, solą i pieprzem, key-streching
- ✓ **(niezbędne)** zabezpieczenie transmisji poprzez wykorzystanie protokołu https,
- ✓ **(niezbędne)** możliwość zmiany hasła,
- ✓ **(niezbędne)** możliwość odzyskania dostępu w przypadku utraty hasła,
- ✓ **(niezbędne)** rejestrowanie nowych pożyczek i podgląd zapisanych danych,
- ✓ dodatkowa kontrola spójności sesji (przeciw atakom XSRF),
- ✓ monitorowanie liczby nieudanych prób logowania,
- ✓ progresywne dodawanie opóźnienia przy weryfikacji hasła w celu wydłużenia ataków zdalnych,
- ✓ informowanie użytkownika o jakości jego hasła (jego entropii),
- ✓ kontrola odporności nowego hasła na ataki słownikowe,
- ✓ informowanie użytkownika o nowych podłączeniach do jego konta.

### Użyte algorytmy i rozwiązania

- Hashowanie hasła: algorytm [scrypt](https://cryptobook.nakov.com/mac-and-key-derivation/scrypt)
- Do sprawdzania odporności został użyty słownik z repozutorium [SecLists](https://github.com/danielmiessler/SecLists/blob/master/Passwords/500-worst-passwords.txt)
- Entropia hasła jest kategoryzowana na podstawie [tego artykułu](https://www.baeldung.com/cs/password-entropy)
- Czas przedłużenia odpowiedzi na podstawie [zmierzonego czasu](###-Czas-odpowiedzi-logowania)

### Czas odpowiedzi logowania

Bez poóźnienia:

```
OK avg time:  6.606372818946839
Bad pass avg time:  4.5753583812713625
No user avg time:  2.042536883354187
```

Z opóźnieniem:

```
OK avg time:  6.699026107788086
Bad pass avg time:  6.622234344482422
No user avg time:  6.775335264205933
```

Kod:

```python
import requests
import time

def login_to_server(username, password):
    url = "http://localhost:5000/login"
    data = {
        'username': username,
        'password': password
    }

    start_time = time.time()
    response = requests.post(url, data=data)
    end_time = time.time()
    return end_time - start_time


oks = []
bad_pass = []
no_usr = []

for _ in range(50):
    time_elapsed = login_to_server("b0b", "ala_ma_K0TA")
    oks.append(time_elapsed)
for _ in range(50):
    time_elapsed = login_to_server("b0b", "ala_ma_K00TA")
    bad_pass.append(time_elapsed)
for _ in range(50):
    time_elapsed = login_to_server("b0000b", "ala_ma_K0TA")
    no_usr.append(time_elapsed)

print("OK avg time: ", sum(oks) / len(oks))
print("Bad pass avg time: ", sum(bad_pass) / len(bad_pass))
print("No user avg time: ", sum(no_usr) / len(no_usr))
```
