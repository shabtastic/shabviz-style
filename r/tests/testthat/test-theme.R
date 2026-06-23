library(testthat)
library(shabvizstyle)

test_that("light range lo is lower than dark range lo for all cmaps", {
  cmaps <- c("viridis", "mako", "rocket", "crest", "flare", "cividis")
  for (cmap in cmaps) {
    light_lo <- shabvizstyle:::.resolve_range(cmap, NULL, NULL, "light")[1]
    dark_lo  <- shabvizstyle:::.resolve_range(cmap, NULL, NULL, "dark")[1]
    expect_true(dark_lo > light_lo,
      label = paste(cmap, ": dark lo", dark_lo, "not > light lo", light_lo))
  }
})

test_that("black uses same range as dark", {
  cmaps <- c("viridis", "mako", "rocket", "crest", "flare", "cividis")
  for (cmap in cmaps) {
    dark  <- shabvizstyle:::.resolve_range(cmap, NULL, NULL, "dark")
    black <- shabvizstyle:::.resolve_range(cmap, NULL, NULL, "black")
    expect_equal(dark, black)
  }
})

test_that("invalid theme raises error", {
  expect_error(shabvizstyle:::.resolve_range("viridis", NULL, NULL, "neon"),
               regexp = "theme")
})

test_that("resolve_range respects lo/hi override", {
  result <- shabvizstyle:::.resolve_range("viridis", 0.1, 0.8, "dark")
  expect_equal(result, c(0.1, 0.8))
})

test_that("palette_sv returns different colors for light vs dark", {
  light_cols <- palette_sv(2, theme = "light")
  dark_cols  <- palette_sv(2, theme = "dark")
  expect_false(identical(light_cols, dark_cols))
})

test_that("palette_sv dark and black return same colors", {
  dark_cols  <- palette_sv(4, theme = "dark")
  black_cols <- palette_sv(4, theme = "black")
  expect_identical(dark_cols, black_cols)
})

test_that("binary_palette returns length-2 for all themes", {
  for (theme in c("light", "dark", "black")) {
    result <- binary_palette(theme = theme)
    expect_length(result, 2)
  }
})

test_that("palette_sv default theme is light", {
  default_cols <- palette_sv(2)
  light_cols   <- palette_sv(2, theme = "light")
  expect_identical(default_cols, light_cols)
})

test_that("binary_palette raises error for invalid theme even when positions supplied", {
  expect_error(binary_palette(positions = c(0.1, 0.9), theme = "neon"),
               regexp = "theme")
})
