from argparse import ArgumentParser
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
sns.set_theme()


def test_statistics(filename: str):
    df = pd.read_csv(filename)
    print(df.sum())


def plot_percentages(data: pd.DataFrame, out: str, name: str):
    labels = data["labels"]
    sizes = data["sizes"]

    plt.pie(sizes, labels=labels, autopct="%1.1f%%")
    plt.title(f"Number of Student Made Gameboards Completed\n{name}")

    plt.show()
    plt.savefig(out)


def plot_gameboard_completion(data: pd.DataFrame, out: str, name: str):
    x = data["x"]
    y = data["y"]
    data_len = len(x)
    log_y = np.log10(data["y"])

    plt.scatter(x[1:data_len-1], log_y[1:data_len-1])
    plt.title(f"Number of Students Against Gameboard Completion\n{name}")
    plt.xlabel("Percentage Complete")
    plt.ylabel("Log Number of Students")

    plt.annotate(f"{y[0]} students attempt with little success.", (x[0], log_y[0]))
    plt.plot(x[0], log_y[0], 'ro')
    plt.annotate(f"{y[data_len-1]} students complete all their gameboards!", (x[data_len-1], log_y[data_len-1]),
                 ha='right')
    plt.plot(x[data_len-1], log_y[data_len-1], 'go')

    plt.show()
    plt.savefig(out)


if __name__=='__main__':
    parser = ArgumentParser()
    parser.add_argument("-g", "--graph", required=True, choices=["scatter", "pie"], help="Graph type")
    parser.add_argument("-f", "--input", required=True, help="Input filename")
    parser.add_argument("-o", "--output", required=True, help="Output directory")

    args = parser.parse_args()
    split = args.input.split(".")[0].split("/")[-1]
    title = " ".join([word.capitalize() for word in split.split("-")])
    print(args.output + "/" + split + ".png")

    df = pd.read_csv(args.input)

    if args.graph == "scatter":
        df = df.rename(columns={"percentage": "x", "count": "y"})
        breakpoint()
        plot_gameboard_completion(df, args.output + "/" + split + ".png", title)
    if args.graph == "pie":
        df = df.rename(columns={"gameboards": "labels", "count": "sizes"})
        plot_percentages(df, args.output + "/" + split + "-complete" + ".png", title)

