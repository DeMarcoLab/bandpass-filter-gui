from codecs import namereplace_errors
import os
import warnings

from magicgui import magicgui
from magicgui.widgets import SpinBox, FloatSpinBox
import napari
from napari.types import ImageData, LayerDataTuple
from napari.layers import Image, Layer
import numpy as np
import skimage.data
import skimage.draw
import skimage.filters
from typing import List


def fourier_mask(image_shape,
                 bandpass_outer_radius: int,
                 bandpass_inner_radius: int = 0,
                 bandpass_sigma: float = None):
    """Create a fourier bandpass mask.

    Parameters
    ----------
    image_shape : tuple
        Shape of the original image array
    bandpass_outer_radius : int
        Outer radius for bandpass filter array.
    bandpass_inner_radius : int
        Inner radius for bandpass filter array, by default 0
    bandpass_sigma : float
        Avoid ringing artifacts by giving the bandpass mask soft edges.

    Returns
    -------
    bandpass_mask : ndarray
        The bandpass image mask.
    """
    bandpass_mask = np.zeros(image_shape)
    r, c = np.array(image_shape) / 2
    inner_circle_rr, inner_circle_cc = skimage.draw.disk(
        (r, c), bandpass_inner_radius, shape=image_shape)
    outer_circle_rr, outer_circle_cc = skimage.draw.disk(
        (r, c), bandpass_outer_radius, shape=image_shape)
    bandpass_mask[outer_circle_rr, outer_circle_cc] = 1.0
    bandpass_mask[inner_circle_rr, inner_circle_cc] = 0.0
    bandpass_mask = np.array(bandpass_mask)
    # fourier space origin should be in the corner
    bandpass_mask = np.roll(bandpass_mask,
                            (np.array(image_shape) / 2).astype(int),
                            axis=(0, 1))
    # Soft edges help avoid ringing artifacts in results
    if bandpass_sigma is not None:
        bandpass_mask = skimage.filters.gaussian(bandpass_mask.astype(float),
                                                 sigma=bandpass_sigma)
    return bandpass_mask


def main():

    viewer = napari.Viewer()
    viewer.add_image(skimage.data.grass().astype('float'), name="grass")

    # grid on 
    viewer.grid.enabled = True
    # heigh = 1
    viewer.grid.shape = (1, 3)

    @magicgui(
        auto_call=True,
        bandpass_inner_radius={"widget_type": "SpinBox", "max": 1000},
        bandpass_outer_radius={"widget_type": "SpinBox", "max": 1000},
        bandpass_sigma={"widget_type": "FloatSpinBox", "max": 1000},
    )
    def bandpass_filter(image: ImageData,
                        bandpass_inner_radius: int = 0,
                        bandpass_outer_radius: int = 75,
                        bandpass_sigma: float = 1.0,
                        ) -> List[LayerDataTuple]:
        if image is not None:
            image = np.fft.fftn(image)
            mask = fourier_mask(image.shape,
                                bandpass_outer_radius=bandpass_outer_radius,
                                bandpass_inner_radius=bandpass_inner_radius,
                                bandpass_sigma=bandpass_sigma)
            bandpass = np.fft.ifftn(mask * image)

            return [(np.real(bandpass), {"name": "filtered"}), (mask.astype(bool), {"name": "mask"})]

    # add the gui to the viewer as a dock widget
    viewer.window.add_dock_widget(bandpass_filter)
    # if a layer gets added or removed, refresh the dropdown choices
    viewer.layers.events.changed.connect(bandpass_filter.reset_choices)

    # viewer = napari.Viewer()
    napari.run()

if __name__=="__main__":
    main()
