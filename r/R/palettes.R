.valid_themes <- c("light", "dark", "black")

## Per-cmap default sample range — light backgrounds.
.range_light <- list(
  viridis = c(0.05, 0.92),
  mako    = c(0.20, 0.92),
  rocket  = c(0.20, 0.92),
  crest   = c(0.10, 0.92),
  flare   = c(0.10, 0.92),
  cividis = c(0.05, 0.95)
)

## Shifted range for dark/black backgrounds — avoids near-black low end.
.range_dark <- list(
  viridis = c(0.30, 0.95),
  mako    = c(0.35, 0.95),
  rocket  = c(0.35, 0.95),
  crest   = c(0.30, 0.95),
  flare   = c(0.30, 0.95),
  cividis = c(0.30, 0.95)
)

.fallback_range_light <- c(0.05, 0.92)
.fallback_range_dark  <- c(0.30, 0.95)

`%||%` <- function(a, b) if (is.null(a)) b else a

.resolve_range <- function(cmap, lo = NULL, hi = NULL, theme = "light") {
  if (!theme %in% .valid_themes) {
    stop(sprintf("theme must be one of %s, got '%s'",
                 paste(shQuote(.valid_themes), collapse = ", "), theme))
  }
  range_table <- if (theme == "light") .range_light else .range_dark
  fallback    <- if (theme == "light") .fallback_range_light else .fallback_range_dark
  default     <- range_table[[cmap]] %||% fallback
  c(if (is.null(lo)) default[1] else lo,
    if (is.null(hi)) default[2] else hi)
}

## Reorder so result starts with both endpoints (max contrast for binary use),
## then fills in by greedy max-min-distance.
.maxdist_reorder <- function(items) {
  n <- length(items)
  if (n <= 2) return(items)
  out <- c(1L, n)
  while (length(out) < n) {
    candidates <- setdiff(seq_len(n), out)
    dists <- vapply(candidates, function(c) min(abs(c - out)), numeric(1))
    out <- c(out, candidates[which.max(dists)])
  }
  items[out]
}

.cmap_function <- function(cmap) {
  switch(cmap,
    viridis = viridisLite::viridis,
    mako    = viridisLite::mako,
    rocket  = viridisLite::rocket,
    plasma  = viridisLite::plasma,
    inferno = viridisLite::inferno,
    magma   = viridisLite::magma,
    cividis = viridisLite::cividis,
    crest   = viridisLite::viridis,
    flare   = viridisLite::rocket,
    stop(sprintf("Unknown cmap '%s'. Try one of: %s", cmap,
                 paste(names(.range_light), collapse = ", ")))
  )
}

#' n perceptually distinct colors from a viridis-family colormap
#'
#' @param n Number of colors.
#' @param ordered If TRUE, return colors in colormap order (ordinal data).
#' @param cmap Sequential colormap name.
#' @param lo,hi Sample range override. NULL uses per-cmap/per-theme defaults.
#' @param theme Color theme: "light", "dark", or "black". Selects the
#'   sampling range table. Default "light".
#' @return Character vector of hex color codes, length n.
#' @export
palette_sv <- function(n, ordered = FALSE, cmap = "viridis",
                       lo = NULL, hi = NULL, theme = "light") {
  if (n < 1) stop("n must be >= 1")

  fn  <- .cmap_function(cmap)
  rng <- .resolve_range(cmap, lo, hi, theme)

  if (n == 1) return(fn(1, begin = 0.5, end = 0.5))

  positions <- seq(rng[1], rng[2], length.out = n)
  colors    <- vapply(positions, function(p) fn(1, begin = p, end = p),
                      character(1))

  if (!ordered) colors <- .maxdist_reorder(colors)
  colors
}

#' High-contrast binary pair from a viridis-family colormap
#'
#' @param cmap Colormap name.
#' @param positions Length-2 numeric in [0,1]. NULL uses per-cmap/per-theme defaults.
#' @param theme Color theme: "light", "dark", or "black". Default "light".
#' @return Length-2 character vector of hex color codes.
#' @export
binary_palette <- function(cmap = "viridis", positions = NULL,
                           theme = "light") {
  fn <- .cmap_function(cmap)
  if (is.null(positions)) {
    positions <- .resolve_range(cmap, NULL, NULL, theme)
  }
  c(fn(1, begin = positions[1], end = positions[1]),
    fn(1, begin = positions[2], end = positions[2]))
}
