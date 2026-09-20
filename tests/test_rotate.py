import numpy as np

from apps.image_viewer.processing.rotate import apply_rotate, apply_rotation


def test_rotate_zero_degrees_returns_same_shape() -> None:
    image = np.zeros((8, 8), dtype=np.uint8)
    image[2:6, 3:5] = 255
    result = apply_rotation(image, 0, "Nearest Neighbor", "Constant Black")
    assert result.image.shape == image.shape
    assert np.array_equal(result.image, image)


def test_rotate_ninety_degrees_preserves_nonzero_pixels() -> None:
    image = np.zeros((9, 9), dtype=np.uint8)
    image[2:7, 4] = 255
    result = apply_rotation(image, 90, "Nearest Neighbor", "Constant Black")
    assert result.image.shape == image.shape
    assert np.count_nonzero(result.image) >= 4



def test_apply_rotate_accepts_a_custom_center() -> None:
    image = np.zeros((10, 10), dtype=np.uint8)
    image[4:6, 4:6] = 255

    result = apply_rotate(image, 45, center=(5.0, 5.0), border_mode="Reflect")

    assert result.image.shape == image.shape
