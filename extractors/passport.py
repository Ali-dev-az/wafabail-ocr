import re


class PassportExtractor:

    def extract(self, text):

        result = {
            "document_type": "passport",
            "passport_number": None,
            "raw_text": text
        }

        patterns = [
            r"\b[A-Z][0-9]{6,9}\b",
            r"\b[A-Z]{2}[0-9]{6,8}\b"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text.upper()
            )

            if match:

                result["passport_number"] = (
                    match.group(0)
                )

                break

        return result