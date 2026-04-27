# Examples

## Example Artifacts and Reproduction Notes

InferEdgeRuntime benchmark JSON files are environment-dependent, so raw benchmark JSON artifacts are not committed to this repository.
The README provides a compact sample Runtime JSON snippet to show the compare-ready shape.

If local Runtime JSON artifacts are available, place them in a local results directory and run:

```bash
poetry run edgebench compare-runtime-dir results/runtime_compare_real_input --report reports/runtime_compare_real_input.md
```

The `results/runtime_compare_real_input` directory is a local reproduction location, not a committed fixture.
InferEdgeRuntime generates benchmark JSON; InferEdgeLab performs grouping, comparison, and reporting.
