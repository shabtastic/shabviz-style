.theme_colors <- list(
  light = list(
    bg          = "white",
    text        = "#333333",
    axis_line   = "#333333",
    legend_bg   = "white",
    legend_edge = "#cccccc",
    strip_text  = "#333333"
  ),
  dark = list(
    bg          = "#1a1a1a",
    text        = "#e0e0e0",
    axis_line   = "#666666",
    legend_bg   = "#1a1a1a",
    legend_edge = "#666666",
    strip_text  = "#e0e0e0"
  ),
  black = list(
    bg          = "#000000",
    text        = "#ffffff",
    axis_line   = "#888888",
    legend_bg   = "#000000",
    legend_edge = "#888888",
    strip_text  = "#ffffff"
  )
)

## Font registry — mirror of shabviz_style._FONT_SOURCES.
.font_sources <- list(
  Inter = list(family = "Inter", google = "Inter"),
  `Source Sans 3` = list(family = "Source Sans 3", google = "Source Sans 3"),
  `IBM Plex Sans` = list(family = "IBM Plex Sans", google = "IBM Plex Sans")
)

#' Install Inter (or another registered font) via sysfonts/showtext
#'
#' @param name Font name from .font_sources. Default "Inter".
#' @return TRUE if the font is now available, FALSE otherwise.
#' @export
install_inter <- function(name = "Inter") {
  if (!name %in% names(.font_sources)) {
    warning(sprintf("Font '%s' is not in the registry.", name))
    return(FALSE)
  }

  if (!.font_available(name)) {
    if (!requireNamespace("sysfonts", quietly = TRUE) ||
        !requireNamespace("showtext", quietly = TRUE)) {
      message(
        "[shabvizstyle] To auto-install fonts, install the 'sysfonts' and ",
        "'showtext' packages:\n",
        "  install.packages(c('sysfonts', 'showtext'))\n",
        "Or install ", name, " system-wide and restart R."
      )
      return(FALSE)
    }
    google_name <- .font_sources[[name]]$google
    tryCatch({
      sysfonts::font_add_google(google_name, name)
      showtext::showtext_auto()
    }, error = function(e) {
      message(sprintf("[shabvizstyle] Could not install %s: %s",
                      name, conditionMessage(e)))
      return(FALSE)
    })
  }
  .font_available(name)
}

.font_available <- function(name) {
  in_system <- name %in% systemfonts::system_fonts()$family
  in_showtext <- if (requireNamespace("sysfonts", quietly = TRUE)) {
    name %in% sysfonts::font_families()
  } else FALSE
  in_system || in_showtext
}

#' shabviz ggplot2 theme
#'
#' @param base_size Base font size in points. Default 11.
#' @param base_family Font family. Default "" tries Inter then falls back.
#' @param theme Color theme: "light", "dark", or "black". Default "light".
#' @return A ggplot2 theme object.
#' @export
theme_shabviz <- function(base_size = 11, base_family = "",
                          theme = "light") {
  if (!theme %in% .valid_themes) {
    stop(sprintf("theme must be one of %s, got '%s'",
                 paste(shQuote(.valid_themes), collapse = ", "), theme))
  }
  c <- .theme_colors[[theme]]

  family <- if (identical(base_family, "")) {
    if (.font_available("Inter")) "Inter" else ""
  } else base_family

  ggplot2::theme_minimal(base_size = base_size, base_family = family) +
    ggplot2::theme(
      text = ggplot2::element_text(colour = c$text),
      plot.title = ggplot2::element_text(size = base_size * 1.18,
                                         face = "plain",
                                         margin = ggplot2::margin(b = 10)),
      plot.subtitle = ggplot2::element_text(size = base_size,
                                            colour = c$text),
      axis.title = ggplot2::element_text(size = base_size, colour = c$text),
      axis.text  = ggplot2::element_text(size = base_size * 0.9,
                                         colour = c$text),
      axis.line  = ggplot2::element_line(colour = c$axis_line, linewidth = 0.4),
      axis.ticks = ggplot2::element_line(colour = c$axis_line, linewidth = 0.4),
      axis.ticks.length = grid::unit(3, "pt"),

      panel.grid.major = ggplot2::element_blank(),
      panel.grid.minor = ggplot2::element_blank(),
      panel.background = ggplot2::element_rect(fill = c$bg, colour = NA),
      plot.background  = ggplot2::element_rect(fill = c$bg, colour = NA),

      legend.position   = "right",
      legend.background = ggplot2::element_rect(fill = c$legend_bg,
                                                colour = c$legend_edge),
      legend.key        = ggplot2::element_blank(),
      legend.title      = ggplot2::element_text(size = base_size * 0.9),
      legend.text       = ggplot2::element_text(size = base_size * 0.9),

      strip.background = ggplot2::element_blank(),
      strip.text = ggplot2::element_text(size = base_size,
                                         colour = c$strip_text,
                                         face = "plain"),

      plot.margin = ggplot2::margin(8, 8, 8, 8)
    )
}

#' Set up shabvizstyle: register theme, default scales, and font
#'
#' @param cmap Base colormap. Default "viridis".
#' @param font Body font. Default "Inter".
#' @param auto_install Whether to attempt auto-installing the font.
#' @param base_size Base font size in points.
#' @param verbose Print status messages.
#' @param theme Color theme: "light", "dark", or "black". Default "light".
#' @export
setup <- function(cmap = "viridis", font = "Inter",
                  auto_install = TRUE, base_size = 11,
                  verbose = FALSE, theme = "light") {
  if (!theme %in% .valid_themes) {
    stop(sprintf("theme must be one of %s, got '%s'",
                 paste(shQuote(.valid_themes), collapse = ", "), theme))
  }

  if (auto_install && font %in% names(.font_sources)) {
    ok <- install_inter(font)
    if (verbose) {
      message(sprintf("[shabvizstyle] %s",
        if (ok) sprintf("%s registered.", font)
        else sprintf("%s not available; using fallback sans-serif.", font)
      ))
    }
  }

  ggplot2::theme_set(theme_shabviz(base_size = base_size,
                                   base_family = if (.font_available(font)) font else "",
                                   theme = theme))

  options(
    ggplot2.discrete.colour = function() scale_colour_shabviz_d(cmap = cmap, theme = theme),
    ggplot2.discrete.fill   = function() scale_fill_shabviz_d(cmap = cmap, theme = theme),
    ggplot2.continuous.colour = function() scale_colour_shabviz_c(cmap = cmap),
    ggplot2.continuous.fill   = function() scale_fill_shabviz_c(cmap = cmap)
  )

  if (verbose) {
    message(sprintf("[shabvizstyle] Theme and scales applied (cmap=%s, font=%s, theme=%s).",
                    cmap, font, theme))
  }
  invisible(NULL)
}
