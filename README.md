# Trunk-Based Development & Feature Flag Demo

このプロジェクトは、Azure App Configurationを用いた動的なフィーチャーフラグ制御（キルスイッチ・ダークローンチ）と、Branch by Abstraction (DI) の実装例を示すデモアプリです。

## 構成
- **Azure Container Instances (ACI)**: アプリケーションの実行環境
- **Azure Container Registry (ACR)**: コンテナイメージの保存先
- **Azure App Configuration**: 設定とフィーチャーフラグの管理（マネージドIDで安全に接続）
- **Python (FastAPI)**: アプリケーション実装

## 手順シナリオ

### 1. デプロイの実行
用意されたスクリプトを実行して、インフラとアプリケーションをAzureにデプロイします。
```bash
./scripts/deploy.sh
```
※完了すると最後に `aciFqdn` (URL) が出力されます。

### 2. 初期動作の確認（ダークローンチ状態）
出力されたURL (`http://<FQDN>/greet`) にブラウザまたは `curl` でアクセスします。
```bash
curl http://<FQDN>/greet
```
**期待される結果:**
```json
{"message": "Hello, World!"}
```
※この時点ではまだフィーチャーフラグがオフであるため、旧ロジックが動作しています。コードはすでに新ロジックを含んで本番にデプロイされています（ダークローンチ）。

### 3. 機能の公開（リリース）
Azure CLI を用いて、Azure App Configuration のフィーチャーフラグを有効（ON）にします。
同時に、アプリに設定の再読み込みを促すために、`Sentinel` キーの値を更新します。

```bash
RG="rg-tbd-demo"
# App Configurationの名前を取得
APP_CONF_NAME=$(az appconfig list -g $RG --query "[0].name" -o tsv)

# 1. フィーチャーフラグを有効にする
az appconfig feature set --name $APP_CONF_NAME --feature GreetingFeature --yes

# 2. Sentinelキーを更新する（動的リフレッシュのトリガー）
az appconfig kv set --name $APP_CONF_NAME --key Sentinel --value $(date +%s) --yes
```

### 4. 動的リフレッシュの確認（リリース完了）
数秒（10〜30秒程度）待ってから、再度エンドポイントにアクセスします。
```bash
curl http://<FQDN>/greet
```
**期待される結果:**
```json
{"message": "🚀 Hello from the New Feature Flag System!"}
```
※コンテナの再起動なしに、動的にロジックが切り替わりました。

### 5. キルスイッチ（ロールバック）の体験
もし新機能に致命的なバグが見つかった場合、同様の手順でフラグをオフにし、Sentinelを更新するだけで、即座に数秒で旧ロジックにロールバックできます。
```bash
az appconfig feature disable --name $APP_CONF_NAME --feature GreetingFeature --yes
az appconfig kv set --name $APP_CONF_NAME --key Sentinel --value $(date +%s) --yes
```
再度 `curl` を実行して、"Hello, World!" に戻ることを確認してください。
