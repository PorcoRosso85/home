#!/bin/bash
# POC検索環境のセットアップ

echo "🔧 Setting up POC search environment..."

# 仮想環境作成
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# 依存関係インストール
echo "Installing dependencies..."
cat > requirements.txt << EOF
kuzu>=0.10.1
sentence-transformers>=2.2.0
pytest>=7.0.0
EOF

source .venv/bin/activate
uv pip install -r requirements.txt

# KuzuDBのライブラリパッチ
echo "Patching KuzuDB libraries..."
for lib in .venv/lib/python*/site-packages/kuzu/*.so; do
    if [ -f "$lib" ]; then
        patchelf --set-rpath "$LD_LIBRARY_PATH:$(patchelf --print-rpath $lib)" "$lib"
    fi
done

echo "✅ Setup complete!"
echo "Activate with: source .venv/bin/activate"