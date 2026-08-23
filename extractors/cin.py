import re


class CINExtractor:

    def extract(self, text):

        result = {
            "document_type": "cin",
            "cin_number": None,
            "raw_text": text
        }

        # Numéro CIN marocain
        patterns = [
            r"\b[A-Z]{1,2}\s?[0-9]{5,7}\b",
            r"\b[A-Z]{1,2}[0-9]{6,7}\b"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text.upper()
            )

            if match:

                result["cin_number"] = (
                    match.group(0)
                    .replace(" ", "")
                )

                break

        return result