# 

# Aplicație de adopție \- HappyTails

In cadrul proiectului voi implementa o platforma pentru adoptația animalelor. Voi ilustra prin tabelul afișat mai jos funcționalitățile majore din această platformă și contribuția fiecărui tip de utilizator (Client \- adoptator/donator, Voluntar \- îngrijitor animale, Administrator \- manager adăpost), precum și procesele automatizate ale sistemului:

| ACȚIUNE | Client | Voluntar | Administrator |
| :---- | :---- | :---- | :---- |
| Adopția unui animal | 1\. Căutare animale disponibile 2\. Completare formular de adopție 3\. Programare vizită la adăpost 4\. Primire mail-uri de: \- Confirmare a completării formularului de adopție \- Aprobare /refuz al cererii de adopție | 1\. Căutare animale disponibile 2\. Confirmarea și participarea la întâlnirea dintre adoptator și animal  3\. Primire mail programare a primei întâlniri dintre adoptator și animal | 1\. Căutare animale disponibile 2\. Aprobare aplicații 3\. Primire mail anunț despre cererea de adopție |
| Donații | 1\. Donații unice prin card / recurente automate (lunare/anuale) 2\. Posibilitatea anulării plății recurente 2\. Primire mail reminder cu 24h înainte de plata recurentă \+ redirecționare anulare |  | 1\. Dashboard cu istoric complet donații |
| Animale disponibile | 1\. Vizualizare animale disponibile 2\. Adăugare animale la favorite 3\. Primire mail reminder de animalele care sunt în lista de favorite | 1\. Completare informații complete (personalitate, poveste) 2\. Încărcare poze animale 3\. Tracking complet istoric (dată sosire, proveniență, vaccinări) | 1\. Înregistrare animale noi cu informații de bază (specie, rasă, vârstă) 2\. Tracking complet istoric (dată sosire, proveniență, vaccinări) |
| Îngrijire animale |  | 1\. Vizualizare dashboard zilnic cu sarcini (plimbări, hrănit, spălat, curățenie) 2\. Marcare activități completate cu timestamp 3\. Raportare probleme/observații (sănătate, comportament) 4\. Calendar personal cu activități programate 5\. Notificări pentru activități neîndeplinite 6\. Alertă urgențe (animal bolnav, incident) 7\. Reminder activități programate 8\. Confirmare acceptare/finalizare task-uri | 1\. Monitorizare status activități (completate/incomplete) 2\. Vizualizare rapoarte probleme 3\. Alertă aplicații noi pending \+ urgențe critice 4\. Notificare activități necompletate  |
| Statistici | 1\. Istoric personal (aplicații, donații, animale adoptate) | 1\. Statistici personale (activități, ore voluntariat) 2\. Istoric activități completate | 1\. Raport adopții (total, rata succes, timp mediu până la adopție) 2\. Raport donații (total, breakdown unice vs recurente, top donatori) 3\. Raport voluntari (performanță, ore, distribuție activități) |
| Management voluntari |  | 1\. Vizualizare profil personal 2\. Setare disponibilitate (zile libere, vacanțe) 3\. Vizualizare statistici personale (ore voluntariat, activități completate) | 1\. Vizualizare profiluri \+ performanța voluntari 2\. Management cont voluntari (activare/dezactivare)  |
| Setări | 1\. Setări cont personal 2\. Preferințe notificări (email, push) | 1\. Setări cont personal 2\. Preferințe notificări (email, push) | 1\. Configurări generale adăpost (nume, contact, program) 2\. Management utilizatori (roluri, permisiuni) 3\. Configurare template-uri email |

Pentru a implementa aceste functionalități, soluția va expune următoarele **rute**:

- Autentificare (**Publice**):

| POST      /login              \- Login utilizator (redirect SSO Keycloak) POST      /logout             \- Logout GET       /callback           \- OAuth callback (Keycloak) |
| :---- |

## API Routes Implementation Status

### Autentificare (Publice)
- [x] `POST /login` - Login utilizator (redirect SSO Keycloak)
- [x] `POST /logout` - Logout
- [x] `GET /callback` - OAuth callback (Keycloak)

### Rute Client
- [x] `GET /animals` - Căutare animale disponibile
- [x] `GET /animals/{id}` - Detalii animal specific
- [ ] `POST /adoptions` - Completare formular de adopție
- [ ] `GET /adoptions` - Istoricul aplicațiilor proprii
- [ ] `POST /adoptions/{id}/schedule` - Programare vizită la adăpost
- [ ] `GET /adoptions/{id}` - Verificare status aplicație (aprobată/respinsă)
- [ ] `POST /donations/one-time` - Donație unică prin card
- [ ] `POST /donations/recurring` - Donație recurentă (lunară/anuală)
- [ ] `GET /donations` - Istoric donații proprii
- [ ] `DELETE /donations/{id}/cancel` - Anulare plată recurentă
- [x] `POST /favorites` - Adăugare animal la favorite
- [x] `GET /favorites` - Lista animale favorite
- [x] `DELETE /favorites/{id}` - Ștergere animal din favorite
- [ ] `GET /client/stats` - Istoric personal (aplicații, donații, animale adoptate)
- [x] `GET /profile` - Setări cont personal
- [ ] `PUT /profile/notifications` - Preferințe notificări (email, push)

### Rute Voluntar
- [x] `GET /animals` - Căutare animale disponibile
- [x] `PUT /animals/edit/{id}` - Actualizare informații animal
- [ ] `GET /visits` - Lista vizite programate (întâlniri adoptator-animal)
- [ ] `POST /visits/{id}/confirm` - Confirmare participare la întâlnire
- [ ] `POST /visits/{id}/report` - Raport post-vizită
- [x] `GET /animals/{id}` - Vizualizare detalii animal
- [x] `PUT /animals/{id}/info` - Completare informații (personalitate, poveste)
- [ ] `GET /animals/{id}/history` - Tracking complet istoric (dată sosire, proveniență, vaccinări)
- [ ] `PUT /animals/{id}/history` - Actualizare istoric (vaccinări, evenimente)
- [x] `GET /dashboard` - Vizualizare dashboard zilnic cu sarcini (plimbări, hrănit, spălat, curățenie)
- [ ] `GET /activities` - Calendar personal cu activități programate
- [ ] `POST /activities/{id}/complete` - Marcare activitate completată cu timestamp
- [ ] `POST /activities/{id}/accept` - Acceptare task din notificare (sistem Be My Eyes)
- [ ] `POST /reports` - Raportare probleme/observații (sănătate, comportament)
- [ ] `GET /reports` - Istoric rapoarte proprii
- [ ] `GET /stats` - Statistici personale (activități, ore voluntariat)
- [ ] `GET /history` - Istoric activități completate
- [x] `GET /profile` - Setări cont personal
- [ ] `PUT /notifications` - Preferințe notificări (email, push)

### Rute Admin
- [x] `GET /animals` - Căutare animale disponibile
- [ ] `GET /adoptions` - Lista toate aplicațiile de adopție
- [ ] `GET /adoptions/{id}` - Detalii aplicație specifică
- [ ] `PUT /adoptions/{id}/approve` - Aprobare aplicație
- [ ] `PUT /adoptions/{id}/reject` - Respingere aplicație
- [ ] `POST /adoptions/{id}/finalize` - Finalizare adopție
- [ ] `GET /donations` - Dashboard cu istoric complet donații
- [ ] `GET /donations/stats` - Statistici donații
- [x] `POST /animals` - Înregistrare animale noi cu informații de bază (specie, rasă, vârstă)
- [x] `PUT /animals/edit/{id}` - Actualizare informații animal
- [x] `DELETE /animals/{id}` - Ștergere animal
- [ ] `GET /animals/{id}/history` - Tracking complet istoric (dată sosire, proveniență, vaccinări)
- [ ] `PUT /animals/{id}/history` - Actualizare istoric
- [ ] `GET /activities` - Monitorizare status activități (completate/necompletate)
- [ ] `GET /activities/pending` - Lista activități necompletate
- [ ] `GET /reports` - Vizualizare rapoarte probleme de la voluntari
- [ ] `PUT /reports/{id}/resolve` - Marcare problemă ca rezolvată
- [ ] `POST /activities` - Creare activitate/task nouă
- [ ] `GET /stats/adoptions` - Raport adopții
- [ ] `GET /stats/donations` - Raport donații
- [ ] `GET /volunteers` - Vizualizare profiluri + performanța voluntari
- [ ] `GET /volunteers/{id}` - Detalii profil voluntar specific
- [ ] `PUT /volunteers/{id}/activate` - Activare cont voluntar
- [ ] `PUT /volunteers/{id}/deactivate` - Dezactivare cont voluntar
- [ ] `GET /settings` - Configurări generale adăpost (nume, contact, program)
- [ ] `PUT /settings` - Actualizare setări generale
- [ ] `GET /users` - Management utilizatori (roluri, permisiuni)
- [ ] `PUT /users/{id}/role` - Modificare rol utilizator
- [ ] `GET /templates` - Configurare template-uri email
- [ ] `PUT /templates/{id}` - Editare template email specific

Funcții avansate:

1. **Sistem Inteligent de Notificări**

Utilizatorii vor primi automat email-uri sau push notifications bazate pe evenimente și condiții predefinite din sistem. Comunicarea între servicii se realizează printr-un broker de mesaje (RabbitMQ) pentru procesare asincronă.  
Sistem "Be My Eyes" pentru voluntari: Inspirat din aplicația Be My Eyes, implementează un algoritm round-robin cu escaladare în 3 runde. Exemplu: Dacă Rex nu a fost plimbat până la ora 17:00, sistemul declanșează notificări în cascadă la interval de 15 minute: Runda 1 \-\> toți voluntarii pe tură primesc notificare (3 voluntari), Runda 2 \-\> după wait time de 15 min, se extinde la toți voluntarii disponibili cu prioritate ridicată, Runda 3 \-\>  administratorii primesc alertă de urgență critică. First step: toată lumea primește notificarea prima dată pentru alegere. Prima persoană care acceptă task-ul oprește cascada.  
Alerte urgențe: Pentru administratori și voluntari, doar urgențele (animal bolnav, incident grav) declanșează notificări instant prin toate canalele disponibile.

2. **Sistem Asincron Management Donații**

Sistemul de plăți funcționează asincron, iar comunicarea între servicii se realizează printr-un broker de mesaje (RabbitMQ sau Kafka). Procesarea donațiilor este gestionată de un microserviciu dedicat care se integrează cu Stripe pentru procesarea plăților.  
Donații recurente cu reminder automat: Pentru subscripțiile recurente (lunare/anuale), sistemul verifică zilnic donațiile programate și utilizatorul este notificat cu 24h înainte de recurență printr-un email care conține un buton de cancel. Email-ul include: detalii sumă, dată charge, și link unic de anulare. Dacă utilizatorul apasă click pe buton, subscripția se anulează automat în Stripe și primește email de confirmare. Dacă nu acționează, plata se procesează automat.
