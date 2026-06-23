## ggplot2 scales — discrete and continuous, color and fill, with the
## per-cmap range defaults baked in.

#' Discrete shabviz color scale
#' @param cmap Colormap name (default "viridis").
#' @param ordered If TRUE, colors are in colormap order.
#' @param lo,hi Sample range. NULL uses per-cmap/per-theme defaults.
#' @param theme Color theme: "light", "dark", or "black". Default "light".
#' @param ... Passed to ggplot2::discrete_scale().
#' @export
scale_colour_shabviz_d <- function(cmap = "viridis", ordered = FALSE,
                                   lo = NULL, hi = NULL,
                                   theme = "light", ...) {
  ggplot2::discrete_scale(
    aesthetics = "colour",
    scale_name = "shabviz_d",
    palette = function(n) palette_sv(n, ordered = ordered, cmap = cmap,
                                     lo = lo, hi = hi, theme = theme),
    ...
  )
}

#' @rdname scale_colour_shabviz_d
#' @export
scale_color_shabviz_d <- scale_colour_shabviz_d

#' Discrete shabviz fill scale
#' @inheritParams scale_colour_shabviz_d
#' @export
scale_fill_shabviz_d <- function(cmap = "viridis", ordered = FALSE,
                                 lo = NULL, hi = NULL,
                                 theme = "light", ...) {
  ggplot2::discrete_scale(
    aesthetics = "fill",
    scale_name = "shabviz_d",
    palette = function(n) palette_sv(n, ordered = ordered, cmap = cmap,
                                     lo = lo, hi = hi, theme = theme),
    ...
  )
}

#' Continuous shabviz color scale
#' @param cmap Colormap name.
#' @param ... Passed to ggplot2::scale_colour_gradientn().
#' @export
scale_colour_shabviz_c <- function(cmap = "viridis", ...) {
  fn <- .cmap_function(cmap)
  ggplot2::scale_colour_gradientn(colours = fn(256), ...)
}

#' @rdname scale_colour_shabviz_c
#' @export
scale_color_shabviz_c <- scale_colour_shabviz_c

#' Continuous shabviz fill scale
#' @inheritParams scale_colour_shabviz_c
#' @export
scale_fill_shabviz_c <- function(cmap = "viridis", ...) {
  fn <- .cmap_function(cmap)
  ggplot2::scale_fill_gradientn(colours = fn(256), ...)
}
