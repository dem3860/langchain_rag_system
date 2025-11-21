from agent import app

def main():
    print("Generating graph image...")
    try:
        # グラフ構造をMermaid形式のPNG画像として取得
        # 注意: デフォルトでは mermaid.ink のAPIを使用するためインターネット接続が必要です
        png_data = app.get_graph().draw_mermaid_png()
        
        output_path = "agent_graph.png"
        with open(output_path, "wb") as f:
            f.write(png_data)
            
        print(f"Successfully saved graph to {output_path}")
        
    except Exception as e:
        print(f"Error generating graph: {e}")
        print("Hint: グラフの描画にはインターネット接続が必要です。")

if __name__ == "__main__":
    main()
