# Éthique et cadre légal

Ce projet reproduit une attaque de **ré-identification de personnes** par
analyse passive des trames Wi-Fi (Beamforming Feedback Information). La
technique est puissante et intrusive : elle permet de reconnaître *qui* se
trouve dans une pièce sans qu'aucun appareil ne soit porté par la cible. Elle
doit être traitée comme une capacité de surveillance.

## Ce qui est autorisé dans ce projet

- Capture **passive** sur **votre propre réseau Wi-Fi**, chez vous.
- Uniquement avec le **consentement explicite et éclairé** de chaque personne
  dont les données servent à entraîner ou tester un modèle.
- À des fins **d'apprentissage et de recherche défensive** (comprendre la
  menace pour mieux s'en protéger).

## Ce qui est strictement exclu

- Capturer ou analyser le trafic d'un réseau qui ne vous appartient pas.
- Observer, profiler ou ré-identifier des tiers **sans leur consentement**
  (voisins, passants, clients d'un lieu public, etc.).
- Déployer le système dans un lieu public ou partagé.
- Publier ou partager un dataset contenant des signatures rattachables à des
  personnes identifiables sans base légale (voir RGPD ci-dessous).
- Toute utilisation visant la surveillance, le pistage ou le ciblage de
  personnes.

## RGPD / données personnelles

Une signature corporelle qui permet de ré-identifier un individu est une
**donnée personnelle**, et probablement une donnée **biométrique** au sens de
l'article 9 du RGPD (catégorie particulière, protection renforcée). En
conséquence :

- Recueillir un **consentement écrit** avant toute collecte.
- Documenter la **finalité** (ici : apprentissage personnel) et la limiter.
- **Minimiser** : ne collecter que le nécessaire, anonymiser les labels.
- Prévoir **suppression** sur demande et une **durée de conservation** courte.
- Ne **jamais** diffuser le dataset brut hors du cercle des personnes
  consentantes.

## Légalité de l'interception

Selon les juridictions, l'interception de communications électroniques — même
de trames de gestion non chiffrées — peut être encadrée par la loi. Le fait
que les BFI soient diffusées en clair ne rend pas leur captation libre dans
tous les contextes. Limitez-vous à votre réseau et à votre foyer.

## Divulgation responsable

Ce travail illustre une faiblese de conception du Wi-Fi (BFI non chiffrées au
niveau MAC). L'objectif est défensif : sensibilisation, et évaluation de
contre-mesures (randomisation, agrégation, chiffrement des trames de gestion,
réduction de la fréquence des soundings). Toute découverte doit servir à
**protéger**, pas à exploiter.

---

En utilisant ce code, vous vous engagez à respecter ce cadre. En cas de doute
sur la légalité d'un usage, abstenez-vous.
