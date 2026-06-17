"""Shared 層（DTO・設定・ジョブ仕様・数値安定化メタなど）。

層外からは ``config`` / ``dto`` / ``job_spec`` / ``numerical_stability`` など
各サブシステムの公開窓口（``__all__`` 付き ``__init__.py``）を正とする。

Note:
    本パッケージルートは束ね用であり、ここからシンボルを import しない。
"""
