from app import Main

if __name__ == '__main__':
    try:
        Main()
    except:
        import sys
        print(sys.exc_info()[0])
        import traceback
        print(traceback.format_exc())
    finally:
        print()
        input("Press enter to exit")
