"""Display faces. Each face is a pure ``render(state) -> framebuffer bytes``.

Faces never read hardware or the clock; they receive an immutable ``RenderState``.
That purity is what lets screenshot-regression tests render any face at any instant.

Phase 0 ships one face (``phase0``) to prove the pipeline and demonstrate the
heartbeat. The eight instrument faces arrive in Phase 3.
"""
