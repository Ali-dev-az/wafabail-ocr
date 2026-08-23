import cv2


def load_image(path):

    image = cv2.imread(path)

    if image is None:
        raise FileNotFoundError(
            f"Image introuvable : {path}"
        )

    return image


def save_image(image, path):

    cv2.imwrite(path, image)


def resize(image, width=None, height=None):

    h, w = image.shape[:2]

    if width:

        ratio = width / w

        new_height = int(h * ratio)

        return cv2.resize(
            image,
            (width, new_height)
        )

    if height:

        ratio = height / h

        new_width = int(w * ratio)

        return cv2.resize(
            image,
            (new_width, height)
        )

    return image


def to_gray(image):

    return cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )


def show(title, image):

    cv2.imshow(title, image)

    cv2.waitKey(0)

    cv2.destroyAllWindows()