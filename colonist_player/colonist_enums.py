
import enum

class ReceivedWSType(enum.Enum):
    Connected = 0
    NewGame = 1
    ContinueGame = 2
    KickedFromGame = 3
    BuildGame = 4
    ChatText = 5
    ChatGameLog = 6
    SessionState = 7
    GameSetup = 8
    CurrentGameState = 9
    BankState = 10
    DiceState = 11
    PlayerControllerState = 12
    AmountOfCardsToDiscard = 13
    MapState = 14
    MapEdges = 15
    MapCorners = 16
    MapTiles = 17
    CardsToSelectForDevelopmentCard = 18
    CardsToSelectForPendingTransaction = 19
    SelectPlayerUsingDevelopmentCard = 20
    ConfirmUseDevelopmentCard = 21
    StealDevelopmentCardFromPlayer = 22
    StealResourceCardFromPlayer = 23
    SelectPlayerAndCard = 24
    SelectCardsToGiveToPlayer = 25
    SelectDice = 26
    ClosePopupUI = 27
    GivePlayerResourcesFromTile = 28
    SelectPlayer = 29
    StoleCard = 30
    GiveCardFromBank = 31
    HighlightCorners = 32
    HighlightRoadEdges = 33
    HighlightShipEdges = 34
    HighlightTiles = 35
    HighlightDiceNumbersForInventor = 36
    BankTradeRatioState = 37
    GetOffer = 38
    EmbargoState = 39
    BoldTextInTradeWindow = 40
    CloseOffer = 41
    OfferError = 42
    OfferRejected = 43
    OfferAccepted = 44
    InfoMessage = 45
    UsedMonopoly = 46
    UsedCards = 47
    ExchangeCards = 48
    DiscardedCards = 49
    LobbyGeneralData = 50
    LobbyPlayerData = 51
    LobbyDisconnectData = 52
    LobbyPublicRooms = 53
    LobbyRoomUpdate = 54
    LobbyRoomRemove = 55
    LobbyGames = 56
    GameSettings = 57
    CustomRoom = 58
    GotKicked = 59
    Banned = 60
    SendPopup = 61
    SendNotification = 62
    SendBroadcast = 63
    GameEndState = 64
    RematchLink = 65
    EndGameText = 66
    SpectatorCount = 67
    SendAnalytics = 68
    PlayersCanceledSpecialBuildPhase = 69
    SpecialBuildPhaseLastPlayerToRollDice = 70
    Vote = 71
    CityImprovementStateUpdated = 72
    ForceShowCityImprovementButtons = 73
    UnlockedCityImprovement = 74
    PlayerReceivedMetropolis = 75
    KnightPieceStateUpdated = 76
    BarbarianStateUpdated = 77
    MerchantStateUpdates = 78
    PlayerReceivedAchievement = 79
    SocketTest = 80
    PlayTurnSound = 81
    PlayersTakingAction = 82
    PlayersDoneTakingAction = 83
    MatchmakingUpdate = 84
    MatchmakingError = 85
    MatchmakingMatchFound = 86


def find_in_enum(data, enum_class):
    """find_in_enum(53, WebSocketMessageType)"""
    for name, member in enum_class.__members__.items():
        if member.value == data:
            return enum_class[name]


class SentType(enum.Enum):
    ChatSubmit = 0
    UpdateNickName = 1
    ClickedLobbyGameListButton = 2
    ClickedLobbyRoomRefreshButton = 3
    ClickedStartTutorial = 4
    ClickedStartFastBots = 5
    ClickedCreateRoom = 6
    ClickedJoinRoom = 7
    AccessGameLink = 8
    ClickedSpectateGame = 9
    ClickedReconnectGame = 10
    ClickedChangeIcon = 11
    EnteredMatchmaking = 12
    ClickedDice = 13
    SelectedTile = 14
    SelectedTiles = 15
    SelectedPlayer = 16
    PassedTurn = 17
    SelectedCards = 18
    BuyDevelopmentCard = 19
    WantToBuildRoad = 20
    ConfirmBuildRoad = 21
    ConfirmRemoveRoad = 22
    WantToBuildSettlement = 23
    ConfirmBuildSettlement = 24
    WantToBuildCity = 25
    ConfirmBuildCity = 26
    WantToBuildShip = 27
    ConfirmBuildShip = 28
    WantToMoveShip = 29
    SelectedShipToMove = 30
    ConfirmMoveShip = 31
    WantToBuildCityWall = 32
    ConfirmBuildCityWall = 33
    WantToPlaceKnight = 34
    ConfirmPlaceKnight = 35
    WantToUpgradeKnight = 36
    ConfirmUpgradeKnight = 37
    WantToActivateKnight = 38
    ConfirmActivateKnight = 39
    WantToTakeKnightAction = 40
    SelectKnightToTakeAction = 41
    ConfirmMoveKnight = 42
    ConfirmMoveKnightOffTurn = 43
    ConfirmRemoveKnight = 44
    ConfirmCityUpgrade = 45
    ConfirmBuildMetropolis = 46
    ConfirmPillageCity = 47
    ConfirmDicePair = 48
    CancelAction = 49
    ClickedDevelpomentCard = 50
    CreatedPlayerOffer = 51
    AcceptedOffer = 52
    TakeAcceptedOffer = 53
    RejectedOffer = 54
    CreatedCounterOffer = 55
    ClickedEmbargo = 56
    RequestActionSwap = 57
    RequestSpecialBuildPhase = 58
    CancelSpecialBuildPhase = 59
    RoomReadyToStart = 60
    RoomSelectColor = 61
    RoomStartGame = 62
    RoomKickPlayer = 63
    RoomAddBot = 64
    RoomSettingChangePrivateGame = 65
    RoomSettingUpdateGameModeSetting = 66
    RoomSettingUpdateMapSetting = 67
    RoomSettingUpdateDiceSetting = 68
    RoomSettingChangeVictoryPointsToWin = 69
    RoomSettingChangeKarmaActive = 70
    RoomSettingChangeCardDiscardLimit = 71
    RoomSettingChangeFriendlyRobber = 72
    RoomSettingChangeMaxPlayers = 73
    RoomSettingChangeHideBankCards = 74
    RoomSettingChangeGameSpeed = 75
    RoomSettingChangeBotSpeed = 76
    ClickedRematch = 77
    Vote = 78
    ClickedFindGame = 79
    ClickedCancelFindGame = 80
    DisconnectedFromSocketServer = 81
    RequestToJoinMatchmakingMatch = 82
    ExitedMatchmaking = 83
    