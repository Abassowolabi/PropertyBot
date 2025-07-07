from mongodb_pipeline import MongoPipeline  # Correct filename reference

def main():
    pipeline = MongoPipeline()
    pipeline.open()
    pipeline.remove_duplicates()
    pipeline.close()

if __name__ == "__main__":
    main()

