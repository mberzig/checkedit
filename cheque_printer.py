#!/usr/bin/env python3
"""
Script pour remplir et imprimer des chèques bancaires sur format A4.
Les positions sont calibrées pour un chèque français standard.

Usage:
    # Ligne de commande
    python cheque_printer.py --montant 150.00 --ordre "Jean Dupont" --lieu Paris

    # Mode interactif
    python cheque_printer.py --interactif

    # Import CSV (plusieurs chèques)
    python cheque_printer.py --csv cheques.csv
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import subprocess
import sys
import os
import argparse
import csv


class ChequePrinter:
    """Classe pour générer et imprimer des chèques."""

    # Positions standard pour un chèque français (en mm depuis le coin bas-gauche)
    # Ces valeurs peuvent nécessiter un ajustement selon votre modèle de chèque
    POSITIONS = {
        'montant_chiffres': {'x': 165, 'y': 75},  # Case montant en chiffres
        'montant_lettres_ligne1': {'x': 25, 'y': 62},  # Première ligne lettres
        'montant_lettres_ligne2': {'x': 25, 'y': 55},  # Deuxième ligne lettres
        'ordre': {'x': 45, 'y': 48},  # Bénéficiaire (à l'ordre de)
        'lieu': {'x': 130, 'y': 35},  # Lieu
        'date': {'x': 155, 'y': 35},  # Date
    }

    # Offset pour positionner le chèque sur la page A4
    # Ajustez ces valeurs selon l'emplacement du chèque sur votre feuille
    CHEQUE_OFFSET = {'x': 10, 'y': 180}  # Position du coin bas-gauche du chèque

    # Dictionnaire pour conversion des nombres en lettres
    UNITES = ['', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf',
              'dix', 'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize', 'dix-sept',
              'dix-huit', 'dix-neuf']
    DIZAINES = ['', 'dix', 'vingt', 'trente', 'quarante', 'cinquante', 'soixante',
                'soixante', 'quatre-vingt', 'quatre-vingt']

    def __init__(self, output_path="cheque.pdf"):
        self.output_path = output_path
        self.page_width, self.page_height = A4

    def nombre_en_lettres(self, nombre):
        """Convertit un nombre en lettres (format français pour chèques en dinars)."""
        if nombre == 0:
            return "zéro dinar"

        # Séparer partie entière et centimes
        dinars = int(nombre)
        centimes = round((nombre - dinars) * 100)

        resultat = self._convertir_nombre(dinars)

        if dinars == 1:
            resultat += " dinar"
        elif dinars > 1:
            resultat += " dinars"

        if centimes > 0:
            resultat += " et " + self._convertir_nombre(centimes)
            if centimes == 1:
                resultat += " centime"
            else:
                resultat += " centimes"

        return resultat.strip()

    def _convertir_nombre(self, n):
        """Convertit un nombre entier en lettres."""
        if n == 0:
            return ""
        if n < 20:
            return self.UNITES[n]
        if n < 100:
            dizaine = n // 10
            unite = n % 10

            if dizaine == 7 or dizaine == 9:
                # 70-79 et 90-99
                base = self.DIZAINES[dizaine]
                if dizaine == 7:
                    if unite == 1:
                        return base + "-et-onze"
                    else:
                        return base + "-" + self.UNITES[10 + unite]
                else:  # 90-99
                    return base + "-" + self.UNITES[10 + unite]
            elif dizaine == 8:
                if unite == 0:
                    return "quatre-vingts"
                else:
                    return "quatre-vingt-" + self.UNITES[unite]
            else:
                if unite == 0:
                    return self.DIZAINES[dizaine]
                elif unite == 1:
                    return self.DIZAINES[dizaine] + "-et-un"
                else:
                    return self.DIZAINES[dizaine] + "-" + self.UNITES[unite]

        if n < 1000:
            centaine = n // 100
            reste = n % 100
            if centaine == 1:
                result = "cent"
            else:
                result = self.UNITES[centaine] + " cent"

            if reste == 0 and centaine > 1:
                result += "s"
            elif reste > 0:
                result += " " + self._convertir_nombre(reste)
            return result

        if n < 1000000:
            millier = n // 1000
            reste = n % 1000
            if millier == 1:
                result = "mille"
            else:
                result = self._convertir_nombre(millier) + " mille"

            if reste > 0:
                result += " " + self._convertir_nombre(reste)
            return result

        if n < 1000000000:
            million = n // 1000000
            reste = n % 1000000
            if million == 1:
                result = "un million"
            else:
                result = self._convertir_nombre(million) + " millions"

            if reste > 0:
                result += " " + self._convertir_nombre(reste)
            return result

        return str(n)  # Fallback pour très grands nombres

    def _formater_montant(self, montant):
        """
        Formate le montant en chiffres avec séparateurs de milliers.
        Ex: 1234567.89 -> "1 234 567,89 DA"
        """
        partie_entiere = int(montant)
        centimes = round((montant - partie_entiere) * 100)

        # Formater avec séparateurs de milliers (espaces)
        partie_entiere_str = f"{partie_entiere:,}".replace(",", " ")

        # Assembler avec centimes
        montant_str = f"{partie_entiere_str},{centimes:02d} DA"

        return montant_str

    def generer_cheque(self, montant, ordre, lieu, date=None):
        """
        Génère un PDF avec les informations du chèque.

        Args:
            montant: Montant en euros (float ou int)
            ordre: Nom du bénéficiaire
            lieu: Lieu d'émission
            date: Date au format JJ/MM/AAAA (défaut: aujourd'hui)
        """
        if date is None:
            date = datetime.now().strftime("%d/%m/%Y")

        c = canvas.Canvas(self.output_path, pagesize=A4)

        # Police pour le chèque
        c.setFont("Helvetica", 10)

        offset_x = self.CHEQUE_OFFSET['x'] * mm
        offset_y = self.CHEQUE_OFFSET['y'] * mm

        # Montant en chiffres (formaté avec séparateurs de milliers)
        montant_str = self._formater_montant(montant)
        pos = self.POSITIONS['montant_chiffres']
        c.drawString(offset_x + pos['x'] * mm, offset_y + pos['y'] * mm, montant_str)

        # Montant en lettres (avec majuscule au début)
        montant_lettres = self.nombre_en_lettres(montant).capitalize()
        # Découper si trop long (limite ~70 caractères par ligne)
        limite_ligne = 70
        if len(montant_lettres) > limite_ligne:
            mots = montant_lettres.split()
            ligne1 = ""
            ligne2 = ""
            sur_ligne2 = False
            for mot in mots:
                if not sur_ligne2 and len(ligne1) + len(mot) < limite_ligne:
                    ligne1 += mot + " "
                else:
                    sur_ligne2 = True
                    ligne2 += mot + " "
            pos1 = self.POSITIONS['montant_lettres_ligne1']
            pos2 = self.POSITIONS['montant_lettres_ligne2']
            c.drawString(offset_x + pos1['x'] * mm, offset_y + pos1['y'] * mm, ligne1.strip())
            c.drawString(offset_x + pos2['x'] * mm, offset_y + pos2['y'] * mm, ligne2.strip())
        else:
            pos = self.POSITIONS['montant_lettres_ligne1']
            c.drawString(offset_x + pos['x'] * mm, offset_y + pos['y'] * mm, montant_lettres)

        # Ordre (bénéficiaire)
        pos = self.POSITIONS['ordre']
        c.drawString(offset_x + pos['x'] * mm, offset_y + pos['y'] * mm, ordre)

        # Lieu
        pos = self.POSITIONS['lieu']
        c.drawString(offset_x + pos['x'] * mm, offset_y + pos['y'] * mm, lieu)

        # Date
        pos = self.POSITIONS['date']
        c.drawString(offset_x + pos['x'] * mm, offset_y + pos['y'] * mm, date)

        c.save()
        print(f"Chèque généré: {self.output_path}")
        return self.output_path

    def imprimer(self, imprimante=None):
        """
        Envoie le PDF à l'imprimante.

        Args:
            imprimante: Nom de l'imprimante (défaut: imprimante par défaut)
        """
        if not os.path.exists(self.output_path):
            print("Erreur: Générez d'abord le chèque avec generer_cheque()")
            return False

        try:
            if sys.platform == "linux":
                cmd = ["lp", self.output_path]
                if imprimante:
                    cmd = ["lp", "-d", imprimante, self.output_path]
            elif sys.platform == "darwin":  # macOS
                cmd = ["lp", self.output_path]
                if imprimante:
                    cmd = ["lp", "-d", imprimante, self.output_path]
            elif sys.platform == "win32":
                # Windows - utilise l'impression par défaut
                os.startfile(self.output_path, "print")
                return True
            else:
                print(f"Plateforme non supportée: {sys.platform}")
                return False

            subprocess.run(cmd, check=True)
            print(f"Chèque envoyé à l'imprimante")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Erreur d'impression: {e}")
            return False
        except Exception as e:
            print(f"Erreur: {e}")
            return False

    def calibration_page(self, output_path="calibration.pdf"):
        """
        Génère une page de calibration avec une grille pour ajuster les positions.
        Imprimez cette page et placez votre chèque dessus pour mesurer les positions.
        """
        c = canvas.Canvas(output_path, pagesize=A4)

        offset_x = self.CHEQUE_OFFSET['x'] * mm
        offset_y = self.CHEQUE_OFFSET['y'] * mm

        # Dessiner le contour d'un chèque standard (175mm x 80mm)
        cheque_width = 175 * mm
        cheque_height = 80 * mm

        # === COINS DE FIXATION (zones pour scotch) ===
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.setLineWidth(0.3)
        coin_size = 15 * mm

        # Coin bas-gauche
        c.rect(offset_x - coin_size, offset_y - coin_size, coin_size, coin_size, fill=1)
        # Coin bas-droit
        c.rect(offset_x + cheque_width, offset_y - coin_size, coin_size, coin_size, fill=1)
        # Coin haut-gauche
        c.rect(offset_x - coin_size, offset_y + cheque_height, coin_size, coin_size, fill=1)
        # Coin haut-droit
        c.rect(offset_x + cheque_width, offset_y + cheque_height, coin_size, coin_size, fill=1)

        # Texte "SCOTCH" dans les coins
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.setFont("Helvetica", 5)
        c.drawString(offset_x - coin_size + 2 * mm, offset_y - coin_size + 5 * mm, "SCOTCH")
        c.drawString(offset_x + cheque_width + 2 * mm, offset_y - coin_size + 5 * mm, "SCOTCH")
        c.drawString(offset_x - coin_size + 2 * mm, offset_y + cheque_height + 5 * mm, "SCOTCH")
        c.drawString(offset_x + cheque_width + 2 * mm, offset_y + cheque_height + 5 * mm, "SCOTCH")

        # === GUIDES D'ALIGNEMENT EN L ===
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(1.5)
        guide_len = 20 * mm

        # L en bas-gauche
        c.line(offset_x, offset_y - 5 * mm, offset_x, offset_y - guide_len)
        c.line(offset_x - 5 * mm, offset_y, offset_x - guide_len, offset_y)

        # L en bas-droit
        c.line(offset_x + cheque_width, offset_y - 5 * mm, offset_x + cheque_width, offset_y - guide_len)
        c.line(offset_x + cheque_width + 5 * mm, offset_y, offset_x + cheque_width + guide_len, offset_y)

        # L en haut-gauche
        c.line(offset_x, offset_y + cheque_height + 5 * mm, offset_x, offset_y + cheque_height + guide_len)
        c.line(offset_x - 5 * mm, offset_y + cheque_height, offset_x - guide_len, offset_y + cheque_height)

        # L en haut-droit
        c.line(offset_x + cheque_width, offset_y + cheque_height + 5 * mm, offset_x + cheque_width, offset_y + cheque_height + guide_len)
        c.line(offset_x + cheque_width + 5 * mm, offset_y + cheque_height, offset_x + cheque_width + guide_len, offset_y + cheque_height)

        # === CONTOUR DU CHÈQUE ===
        c.setStrokeColorRGB(0, 0, 1)
        c.setLineWidth(0.5)
        c.rect(offset_x, offset_y, cheque_width, cheque_height)

        # Grille tous les 10mm
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.setLineWidth(0.2)

        for x in range(0, 176, 10):
            c.line(offset_x + x * mm, offset_y, offset_x + x * mm, offset_y + cheque_height)
            c.setFont("Helvetica", 6)
            c.drawString(offset_x + x * mm, offset_y - 3 * mm, str(x))

        for y in range(0, 81, 10):
            c.line(offset_x, offset_y + y * mm, offset_x + cheque_width, offset_y + y * mm)
            c.drawString(offset_x - 8 * mm, offset_y + y * mm, str(y))

        # Marquer les positions actuelles
        c.setFillColorRGB(1, 0, 0)
        c.setFont("Helvetica", 8)

        for nom, pos in self.POSITIONS.items():
            x = offset_x + pos['x'] * mm
            y = offset_y + pos['y'] * mm
            c.circle(x, y, 2, fill=1)
            c.drawString(x + 3, y + 3, nom)

        # Instructions
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 12)
        c.drawString(20 * mm, 270 * mm, "Page de calibration - Chèque")
        c.setFont("Helvetica", 9)
        c.drawString(20 * mm, 258 * mm, "1. Imprimez cette page")
        c.drawString(20 * mm, 253 * mm, "2. Fixez le chèque avec du scotch repositionnable sur les zones grises")
        c.drawString(20 * mm, 248 * mm, "3. Alignez les bords du chèque avec les guides en L noirs")
        c.drawString(20 * mm, 243 * mm, "4. Notez les positions réelles de chaque champ sur la grille")
        c.drawString(20 * mm, 238 * mm, "5. Ajustez les valeurs dans POSITIONS et CHEQUE_OFFSET")

        c.save()
        print(f"Page de calibration générée: {output_path}")
        return output_path


def mode_interactif():
    """Mode interactif : pose les questions une par une."""
    print("\n=== Remplissage de chèque (mode interactif) ===\n")

    while True:
        try:
            montant_str = input("Montant (en euros, ex: 150.50) : ").strip().replace(',', '.')
            montant = float(montant_str)
            break
        except ValueError:
            print("Erreur: Entrez un nombre valide (ex: 150.50)")

    ordre = input("Ordre (bénéficiaire) : ").strip()
    lieu = input("Lieu : ").strip()

    date_str = input("Date (JJ/MM/AAAA, Entrée pour aujourd'hui) : ").strip()
    if not date_str:
        date_str = datetime.now().strftime("%d/%m/%Y")

    output = input("Nom du fichier PDF (Entrée pour 'cheque.pdf') : ").strip()
    if not output:
        output = "cheque.pdf"

    printer = ChequePrinter(output)
    printer.generer_cheque(montant=montant, ordre=ordre, lieu=lieu, date=date_str)

    # Afficher le montant en lettres
    print(f"\nMontant en lettres: {printer.nombre_en_lettres(montant)}")

    imprimer = input("\nImprimer maintenant ? (o/N) : ").strip().lower()
    if imprimer == 'o':
        printer.imprimer()

    ouvrir = input("Ouvrir le PDF ? (O/n) : ").strip().lower()
    if ouvrir != 'n':
        if sys.platform == "linux":
            subprocess.run(["xdg-open", output])
        elif sys.platform == "darwin":
            subprocess.run(["open", output])
        elif sys.platform == "win32":
            os.startfile(output)

    return printer


def importer_csv(csv_path, output_dir="cheques_generes"):
    """
    Importe plusieurs chèques depuis un fichier CSV.

    Format CSV attendu (avec en-têtes, séparateur point-virgule):
        montant;ordre;lieu;date
        1250000,50;Sonatrach;Alger;07/01/2026
        2345678,75;Marie Martin;Lyon;

    La colonne 'date' est optionnelle (utilise la date du jour si vide).
    """
    if not os.path.exists(csv_path):
        print(f"Erreur: Fichier '{csv_path}' introuvable")
        return []

    # Créer le dossier de sortie
    os.makedirs(output_dir, exist_ok=True)

    cheques_generes = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')

        for i, row in enumerate(reader, 1):
            try:
                montant = float(row['montant'].replace(',', '.').strip())
                ordre = row['ordre'].strip()
                lieu = row['lieu'].strip()
                date = row.get('date', '').strip() or datetime.now().strftime("%d/%m/%Y")

                # Nom de fichier sécurisé
                nom_fichier = f"cheque_{i:03d}_{ordre[:20].replace(' ', '_')}.pdf"
                output_path = os.path.join(output_dir, nom_fichier)

                printer = ChequePrinter(output_path)
                printer.generer_cheque(montant=montant, ordre=ordre, lieu=lieu, date=date)
                cheques_generes.append(output_path)

                print(f"  [{i}] {montant:.2f}€ -> {ordre}")

            except (KeyError, ValueError) as e:
                print(f"  [!] Ligne {i} ignorée: {e}")

    print(f"\n{len(cheques_generes)} chèque(s) généré(s) dans '{output_dir}/'")
    return cheques_generes


def creer_csv_exemple():
    """Crée un fichier CSV d'exemple (séparateur point-virgule)."""
    exemple = """montant;ordre;lieu;date
150,00;Jean Dupont;Paris;07/01/2026
1234,56;Marie Martin;Lyon;
89,99;Boulangerie du Coin;Marseille;15/01/2026
500,00;EDF;Toulouse;"""

    with open("cheques_exemple.csv", 'w', encoding='utf-8') as f:
        f.write(exemple)

    print("Fichier 'cheques_exemple.csv' créé (séparateur: point-virgule).")
    print("Modifiez-le puis lancez: python cheque_printer.py --csv cheques_exemple.csv")


def main():
    parser = argparse.ArgumentParser(
        description="Générateur de chèques bancaires",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python cheque_printer.py --montant 150 --ordre "Jean Dupont" --lieu Paris
  python cheque_printer.py --interactif
  python cheque_printer.py --csv cheques.csv
  python cheque_printer.py --calibration
  python cheque_printer.py --exemple-csv
        """
    )

    # Mode de fonctionnement
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('-i', '--interactif', action='store_true',
                      help="Mode interactif (questions/réponses)")
    mode.add_argument('--csv', metavar='FICHIER',
                      help="Importer les chèques depuis un fichier CSV")
    mode.add_argument('--calibration', action='store_true',
                      help="Générer la page de calibration")
    mode.add_argument('--exemple-csv', action='store_true',
                      help="Créer un fichier CSV d'exemple")

    # Arguments pour un chèque unique
    parser.add_argument('-m', '--montant', type=float,
                        help="Montant en euros")
    parser.add_argument('-o', '--ordre', type=str,
                        help="Nom du bénéficiaire")
    parser.add_argument('-l', '--lieu', type=str,
                        help="Lieu d'émission")
    parser.add_argument('-d', '--date', type=str,
                        help="Date (JJ/MM/AAAA), défaut: aujourd'hui")
    parser.add_argument('--output', '-O', type=str, default="cheque.pdf",
                        help="Nom du fichier PDF de sortie")
    parser.add_argument('--imprimer', '-p', action='store_true',
                        help="Imprimer directement après génération")
    parser.add_argument('--ouvrir', action='store_true',
                        help="Ouvrir le PDF après génération")

    args = parser.parse_args()

    # Mode calibration
    if args.calibration:
        printer = ChequePrinter()
        printer.calibration_page()
        subprocess.run(["xdg-open", "calibration.pdf"])
        return

    # Créer CSV exemple
    if args.exemple_csv:
        creer_csv_exemple()
        return

    # Mode interactif
    if args.interactif:
        mode_interactif()
        return

    # Mode CSV
    if args.csv:
        print(f"\nImport depuis '{args.csv}':\n")
        importer_csv(args.csv)
        return

    # Mode ligne de commande (chèque unique)
    if args.montant and args.ordre and args.lieu:
        printer = ChequePrinter(args.output)
        printer.generer_cheque(
            montant=args.montant,
            ordre=args.ordre,
            lieu=args.lieu,
            date=args.date
        )

        print(f"Montant en lettres: {printer.nombre_en_lettres(args.montant)}")

        if args.imprimer:
            printer.imprimer()

        if args.ouvrir:
            if sys.platform == "linux":
                subprocess.run(["xdg-open", args.output])
            elif sys.platform == "darwin":
                subprocess.run(["open", args.output])
            elif sys.platform == "win32":
                os.startfile(args.output)
        return

    # Aucun argument : afficher l'aide
    parser.print_help()
    print("\n--- Astuce: Utilisez --interactif pour le mode guidé ---")


if __name__ == "__main__":
    main()
