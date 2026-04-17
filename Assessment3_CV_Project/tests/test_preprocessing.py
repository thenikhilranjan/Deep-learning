import numpy as np

from sar_vision.preprocessing import PreprocessOptions, apply_preprocessing, tile_image


def test_apply_preprocessing_runs_selected_steps():
    image = np.random.randint(0, 255, (48, 48, 3), dtype=np.uint8)
    options = PreprocessOptions(
        normalize_thermal=True,
        apply_clahe=True,
        denoise=True,
        denoise_method="median",
        resize_to=(64, 64),
        grayscale=True,
    )

    processed, steps = apply_preprocessing(image, options)

    assert processed.shape == (64, 64)
    assert "thermal_normalization" in steps
    assert "clahe" in steps
    assert "denoise:median" in steps
    assert "grayscale" in steps


def test_tile_image_returns_multiple_tiles_for_large_input():
    image = np.zeros((800, 800), dtype=np.uint8)
    tiles = tile_image(image, tile_size=(320, 320), overlap=0.25)

    assert len(tiles) > 1
    assert all(tile["tile"].shape[0] <= 320 for tile in tiles)
    assert all(tile["tile"].shape[1] <= 320 for tile in tiles)
