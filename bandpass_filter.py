import os
import warnings

from magicgui import magicgui
from magicgui._qt import QSlider, QDoubleSpinBox, QSpinBox, QDoubleSpinBox
import napari
from napari.layers import Image
import numpy as np
import skimage.data
import skimage.draw
import skimage.filters


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
    inner_circle_rr, inner_circle_cc = skimage.draw.circle(
        r, c, bandpass_inner_radius, shape=image_shape)
    outer_circle_rr, outer_circle_cc = skimage.draw.circle(
        r, c, bandpass_outer_radius, shape=image_shape)
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
    with napari.gui_qt():
        viewer = napari.Viewer()
        viewer.add_image(skimage.data.grass().astype('float'), name="grass")

        @magicgui(
            auto_call=True,
            bandpass_inner_radius={"widget_type": QSpinBox, "maximum": 1000},
            bandpass_outer_radius={"widget_type": QSpinBox, "maximum": 1000},
            bandpass_sigma={"widget_type": QDoubleSpinBox, "maximum": 1000},
        )
        def bandpass_filter(layer: Image,
                            bandpass_inner_radius: int = 0,
                            bandpass_outer_radius: int = 75,
                            bandpass_sigma: float = 1.0) -> Image:
            if layer:
                image = np.fft.fftn(layer.data)
                mask = fourier_mask(layer.shape,
                                    bandpass_outer_radius=bandpass_outer_radius,
                                    bandpass_inner_radius=bandpass_inner_radius,
                                    bandpass_sigma=bandpass_sigma)
                image = np.fft.ifftn(mask * image)
                return np.real(image)

        # instantiate the widget
        gui = bandpass_filter.Gui()
        # add the gui to the viewer as a dock widget
        viewer.window.add_dock_widget(gui)
        # if a layer gets added or removed, refresh the dropdown choices
        viewer.layers.events.changed.connect(lambda x: gui.refresh_choices("layer"))


if __name__=="__main__":
    main()
