# ChequEdit

Générateur et imprimeur de chèques bancaires en Python. Remplit automatiquement les chèques avec le montant en chiffres et en lettres, puis génère un PDF prêt à imprimer sur format A4.

## Fonctionnalités

- Conversion automatique du montant en lettres (français)
- Formatage du montant avec séparateurs de milliers (ex: 1 234 567,89 DA)
- Support des dinars algériens (DA)
- Trois modes d'entrée des données :
  - Ligne de commande
  - Mode interactif
  - Import CSV (lots de chèques)
- Page de calibration pour ajuster les positions
- Impression directe

## Installation

```bash
# Cloner le repository
git clone https://github.com/VOTRE_USERNAME/checkedit.git
cd checkedit

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## Utilisation

### Ligne de commande (chèque unique)

```bash
python cheque_printer.py -m 1500000 -o "Sonatrach" -l Alger --ouvrir
```

Options :
| Option | Description |
|--------|-------------|
| `-m, --montant` | Montant en dinars |
| `-o, --ordre` | Bénéficiaire |
| `-l, --lieu` | Lieu d'émission |
| `-d, --date` | Date (JJ/MM/AAAA), défaut: aujourd'hui |
| `-O, --output` | Nom du fichier PDF |
| `--ouvrir` | Ouvre le PDF après génération |
| `-p, --imprimer` | Imprime directement |

### Mode interactif

```bash
python cheque_printer.py --interactif
```

Le script pose les questions une par une.

### Import CSV (plusieurs chèques)

```bash
# Créer un fichier CSV exemple
python cheque_printer.py --exemple-csv

# Importer les chèques
python cheque_printer.py --csv cheques.csv
```

Format CSV (séparateur: point-virgule) :
```csv
montant;ordre;lieu;date
1250000,50;Sonatrach;Alger;07/01/2026
2345678,75;Banque Nationale;Oran;
```

### Calibration

Avant la première utilisation, imprimez la page de calibration pour ajuster les positions selon votre modèle de chèque :

```bash
python cheque_printer.py --calibration
```

1. Imprimez la page de calibration
2. Fixez votre chèque avec du scotch sur les zones grises
3. Alignez les bords avec les guides en L
4. Ajustez les valeurs `POSITIONS` et `CHEQUE_OFFSET` dans le script

## Exemple de sortie

```
Montant: 1 234 567,89 DA
En lettres: Un million deux cent trente-quatre mille cinq cent soixante-sept dinars et quatre-vingt-neuf centimes
```

## Dépendances

- Python 3.8+
- ReportLab

## Licence

MIT License
