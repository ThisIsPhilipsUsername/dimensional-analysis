# Dimensional Analysis: Taylor Blast Wave
https://dimensional-analysis-malwytmt2etclzv2ahp4jf.streamlit.app/

This project explores the classic Taylor blast-wave idea using a photograph sequence of an explosion.

## Historical Context

The photograph sequence used here appears to be intended as the famous **Trinity** blast sequence, the first nuclear weapon test carried out by the Manhattan Project.

- **Date:** July 16, 1945
- **Location:** Jornada del Muerto desert, New Mexico
- **Device:** plutonium implosion device ("the Gadget")
- **Blast size:** approximately **21 kilotons of TNT equivalent**

That historical context is important because G. I. Taylor's famous blast-wave analysis was based on photographs of the Trinity explosion with visible time stamps and a scale reference.

Note:
- The local file `blast.png` in this repo does not include embedded source metadata or a citation.
- So the image is best described as **apparently representing the Trinity test sequence**, rather than being definitively documented in this repository.

## Files

- [Taylor_blast_wave_year12_explanation_upgraded.ipynb](</g:/My Drive/Github/Philip/dimensional analysis/Taylor_blast_wave_year12_explanation_upgraded.ipynb>)
  Full teaching notebook with derivation, scaling, measurement discussion, and energy estimates.

- [Taylor_blast_wave_experiment_only.ipynb](</g:/My Drive/Github/Philip/dimensional analysis/Taylor_blast_wave_experiment_only.ipynb>)
  Shorter notebook focused only on the experimental workflow:
  photo, calibration, measured radii, tolerance checks, and explosion energy estimate.

- [streamlit_app.py](</g:/My Drive/Github/Philip/dimensional analysis/streamlit_app.py>)
  Interactive app with a toggle between measuring radius to the `sides` or to the `top`, plus the best-fit graph and kiloton estimate.

- [blast.png](</g:/My Drive/Github/Philip/dimensional analysis/blast.png>)
  Explosion contact-sheet image used by the notebooks and app.

## Streamlit App

Run:

```bash
streamlit run streamlit_app.py
```

The app lets you:

- switch between `sides` and `top` measurements
- view the best-fit curve with fixed `t^(2/5)` scaling
- see the estimated yield in kilotons TNT
- inspect frame-by-frame values

## Notes

- The scaling law tests whether the measured radius behaves like `r ∝ t^(2/5)`.
- The absolute energy estimate is much more sensitive, because it depends on `r^5`.
- Changing how the radius is measured can shift the inferred kiloton yield a lot.
