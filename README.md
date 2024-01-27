# security-project

Prosta aplikację do ewidencji pożyczek. -- Jest grupa użytkowników, którzy chcą pożyczać pomiędzy sobą dowolne kwoty pieniędzy. Chcą zapisywać, kto komu i ile do kiedy pożyczył pieniędzy. Zakładamy, że pożyczający jest dodaje wpis, pożyczkobiorca potwierdza go i ma tylko jego podgląd, a wszyscy pozostali widzą tylko sumaryczne zadłużenie każdej osoby i czy są długi po terminie spłaty.

## Zakres wymagań

- ✓ **(niezbędne)** restrykcyjna walidacja danych pochodzących z formularza login-hasło,
- ✓ **(niezbędne)** przechowywanie hasła chronione funkcją hash, solą i pieprzem, key-streching
- ✓ **(niezbędne)** zabezpieczenie transmisji poprzez wykorzystanie protokołu https,
- ✓ **(niezbędne)** możliwość zmiany hasła,
- ✓ **(niezbędne)** możliwość odzyskania dostępu w przypadku utraty hasła,
- ✓ **(niezbędne)** rejestrowanie nowych pożyczek i podgląd zapisanych danych,
- dodatkowa kontrola spójności sesji (przeciw atakom XSRF),
- ✓ monitorowanie liczby nieudanych prób logowania,
- progresywne dodawanie opóźnienia przy weryfikacji hasła w celu wydłużenia ataków zdalnych,
- informowanie użytkownika o jakości jego hasła (jego entropii),
- ✓ kontrola odporności nowego hasła na ataki słownikowe,
- ✓ informowanie użytkownika o nowych podłączeniach do jego konta.

### Użyte algorytmy i rozwiązania

- Hashowanie hasła: algorytm [scrypt](https://cryptobook.nakov.com/mac-and-key-derivation/scrypt)
- Do sprawdzania odporności został użyty słownik z repozutorium [SecLists](https://github.com/danielmiessler/SecLists/blob/master/Passwords/500-worst-passwords.txt)


✕