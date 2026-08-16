# saiverse-addon-registry

SAIVerse 本体の「アドオン管理 > カタログ」UI に表示されるアドオンの公式
レジストリです。

このリポジトリは SAIVerse メンテナ ([@maha0525](https://github.com/maha0525)) が
キュレーションしており、ここに掲載されたアドオンのみが SAIVerse UI から
ワンタッチで導入可能になります。

## なぜキュレーション制か

`expansion_data/` 配下のアドオンは Python コードとして自由に SAIVerse の
ランタイムにロードされ、`api_routes.py` や `server_hooks` を経由して本体の
処理に干渉できます。任意の GitHub URL を UI から導入できるようにしてしまうと、
悪意あるリポジトリの混入経路を作ってしまいます。

そのため、**SAIVerse 本体が読みに来るのはこのリポジトリの `registry.json`
のみ**で、ここに掲載されていないアドオンは UI から導入できない仕様にして
います。CLI で `git clone` する経路は引き続き使えます (開発者向け)。

## アドオン作者へ

自作アドオンを registry に掲載してほしい場合は [@maha0525](https://github.com/maha0525) に Issue
または PR を出してください。レビュー基準:

- 公開リポジトリ (public) であること
- `addon.json` が SAIVerse の manifest スキーマ v2 に準拠していること
- setup ステップは [SAIVerse 側 allowlist](https://github.com/maha0525/SAIVerse/blob/main/docs/intent/addon_catalog_management.md) の type のみを使うこと
- 各バージョンは commit SHA で pin されること (ブランチ追従不可)
- ライセンスが明示されていること
- 永続データは `~/.saiverse/user_data/addon_data/<addon_id>/` 配下に置くこと

## registry.json スキーマ

詳細は SAIVerse 本体の
[`docs/intent/addon_catalog_management.md`](https://github.com/maha0525/SAIVerse/blob/main/docs/intent/addon_catalog_management.md)
を参照。

```json
{
    "schema_version": 1,
    "updated_at": "ISO 8601",
    "addons": [
        {
            "id": "アドオン ID (= expansion_data/<id>/)",
            "display_name": "UI 表示名",
            "description": "...",
            "category": "voice | vessel | social | persona | ...",
            "repo_url": "https://github.com/.../<repo>.git",
            "versions": [
                {
                    "version": "セマンティックバージョン",
                    "commit": "commit SHA (7-40 hex)",
                    "setup_version": 1,
                    "min_saiverse_version": "0.2.0",
                    "released_at": "ISO 8601",
                    "changelog_url": "https://github.com/..."
                }
            ],
            "latest": "最新バージョン文字列",
            "icon_url": "https://...",
            "requires": {
                "gpu": "required | optional | none",
                "disk_gb": 6,
                "os": ["windows", "linux", "macos"]
            }
        }
    ]
}
```

## 署名について

SAIVerse 本体は、この公式レジストリからの応答に **Ed25519 署名を必須**として
います (サプライチェーン防御)。配信される `registry.json` は署名済み envelope
形式 (`{"signed": <中身>, "signature": {...}}`) で、対応する公開鍵は SAIVerse
本体に焼き込まれています。

- 人間が編集するのは **`registry.payload.json`** (無署名の中身) のみ
- `registry.json` は `sign_registry.py` が生成する。**手で編集しない**
- 秘密鍵はこのリポジトリには存在しない (メンテナがローカル保管)

## バージョン追加の手順

1. 対象アドオンの新バージョンを GitHub Release として publish (タグ付き)
2. このリポジトリの `registry.payload.json` の対象 `addons[].versions[]` に新エントリを追加
3. `latest` を新バージョンに更新
4. `updated_at` を更新
5. 署名して envelope を再生成:

   ```
   python sign_registry.py --key <秘密鍵ファイルへのパス>
   ```

6. `registry.payload.json` と `registry.json` を両方コミット & push

SAIVerse 本体は最大 5 分のメモリキャッシュを持つので、本番反映には少し時間が
かかります。即時反映したい場合は SAIVerse 側で「カタログ更新」を手動実行。
