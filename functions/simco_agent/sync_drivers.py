from simco_agent.core.sync_manager import SyncManager

def main():
    print("SIMCO AI: Starting Driver Sync...")
    manager = SyncManager()
    manager.sync()
    print("SIMCO AI: Driver Sync Complete.")

if __name__ == "__main__":
    main()
