"""ジョブ投入型 Web 面（FastAPI + Streamlit + SQLAlchemy）。

engine は 1 行も変更しない。計算は ``runner/run_*.py`` を subprocess で起動し、
成果物はファイル経由（``dump_base_dir`` 配下）で受け渡す。詳細は
``docs/apps/web/0_overview.md`` を参照。

サブパッケージの依存方向（上から下への一方向のみ）:

    ui (Streamlit) --HTTP--> api (FastAPI) --> store (SQLAlchemy)
                                             --> runner_gateway --subprocess--> runner/run_*.py
                                             --> engine_contract
"""
