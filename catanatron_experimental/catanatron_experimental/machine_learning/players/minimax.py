import time
import random
from typing import Any

from catanatron.state_functions import (
    get_longest_road_length,
    get_played_dev_cards,
    get_player_buildings,
    player_key,
    player_num_dev_cards,
    player_num_resource_cards,
)
from catanatron.game import Game
from catanatron.models.player import Player
from catanatron.models.actions import ActionType
from catanatron.models.enums import RESOURCES, BuildingType
from catanatron_gym.features import (
    build_production_features,
    reachability_features,
    resource_hand_features,
)
from catanatron_experimental.machine_learning.players.tree_search_utils import (
    expand_spectrum,
)

TRANSLATE_VARIETY = 4  # i.e. each new resource is like 4 production points

DEFAULT_WEIGHTS = {
    # Where to place. Note winning is best at all costs
    "public_vps": 3e14,
    "production": 1e8,
    "enemy_production": -1e8,
    "num_tiles": 1,
    # Towards where to expand and when
    "reachable_production_0": 0,
    "reachable_production_1": 1e4,
    "buildable_nodes": 1e3,
    "longest_road": 10,
    # Hand, when to hold and when to use.
    "hand_synergy": 1e2,
    "hand_resources": 1,
    "discard_penalty": -5,
    "hand_devs": 10,
    "army_size": 10.1,
}

# Change these to play around with new values
CONTENDER_WEIGHTS = {
    "public_vps": 300000000000001.94,
    "production": 100000002.04188395,
    "enemy_production": -99999998.03389844,
    "num_tiles": 2.91440418,
    "reachable_production_0": 2.03820085,
    "reachable_production_1": 10002.018773150001,
    "buildable_nodes": 1001.86278466,
    "longest_road": 12.127388499999999,
    "hand_synergy": 102.40606877,
    "hand_resources": 2.43644327,
    "discard_penalty": -3.00141993,
    "hand_devs": 10.721669799999999,
    "army_size": 12.93844622,
}


class ValueFunctionPlayer(Player):
    """
    Player that selects the move that maximizes a heuristic value function.

    For now, the base value function only considers 1 enemy player.
    """

    def __init__(
        self, color, value_fn_builder_name=None, params=None, is_bot=True, epsilon=None
    ):
        super().__init__(color, is_bot)
        self.value_fn_builder_name = (
            "contender_fn" if value_fn_builder_name == "C" else "base_fn"
        )
        self.params = params
        self.epsilon = epsilon

    def decide(self, game, playable_actions):
        if len(playable_actions) == 1:
            return playable_actions[0]

        if self.epsilon is not None and random.random() < self.epsilon:
            return random.choice(playable_actions)

        best_value = float("-inf")
        best_action = None
        for action in playable_actions:
            game_copy = game.copy()
            game_copy.execute(action)

            value_fn = get_value_fn(self.value_fn_builder_name, self.params)
            value = value_fn(game_copy, self.color)
            if value > best_value:
                best_value = value
                best_action = action

        return best_action

    def __str__(self):
        return super().__str__() + f"(value_fn={self.value_fn_builder_name})"


def get_value_fn(name, params, value_function=None):
    if value_function is not None:
        return value_function
    elif name == "base_fn":
        return base_fn(DEFAULT_WEIGHTS)
    elif name == "contender_fn":
        return contender_fn(params)
    else:
        raise ValueError


def base_fn(params=DEFAULT_WEIGHTS):
    def fn(game, p0_color):
        production_features = build_production_features(True)
        our_production_sample = production_features(game, p0_color)
        enemy_production_sample = production_features(game, p0_color)
        production = value_production(our_production_sample, "P0")
        enemy_production = value_production(enemy_production_sample, "P1", False)

        key = player_key(game.state, p0_color)
        longest_road_length = get_longest_road_length(game.state, p0_color)

        reachability_sample = reachability_features(game, p0_color, 2)
        features = [f"P0_0_ROAD_REACHABLE_{resource}" for resource in RESOURCES]
        reachable_production_at_zero = sum([reachability_sample[f] for f in features])
        features = [f"P0_1_ROAD_REACHABLE_{resource}" for resource in RESOURCES]
        reachable_production_at_one = sum([reachability_sample[f] for f in features])

        hand_sample = resource_hand_features(game, p0_color)
        features = [f"P0_{resource}_IN_HAND" for resource in RESOURCES]
        distance_to_city = (
            max(2 - hand_sample["P0_WHEAT_IN_HAND"], 0)
            + max(3 - hand_sample["P0_ORE_IN_HAND"], 0)
        ) / 5.0  # 0 means good. 1 means bad.
        distance_to_settlement = (
            max(1 - hand_sample["P0_WHEAT_IN_HAND"], 0)
            + max(1 - hand_sample["P0_SHEEP_IN_HAND"], 0)
            + max(1 - hand_sample["P0_BRICK_IN_HAND"], 0)
            + max(1 - hand_sample["P0_WOOD_IN_HAND"], 0)
        ) / 4.0  # 0 means good. 1 means bad.
        hand_synergy = (2 - distance_to_city - distance_to_settlement) / 2

        num_in_hand = player_num_resource_cards(game.state, p0_color)
        discard_penalty = params["discard_penalty"] if num_in_hand > 7 else 0

        # blockability
        buildings = game.state.buildings_by_color[p0_color]
        owned_nodes = buildings[BuildingType.SETTLEMENT] + buildings[BuildingType.CITY]
        owned_tiles = set()
        for n in owned_nodes:
            owned_tiles.update(game.state.board.map.adjacent_tiles[n])
        num_tiles = len(owned_tiles)

        # TODO: Simplify to linear(?)
        num_buildable_nodes = len(game.state.board.buildable_node_ids(p0_color))
        longest_road_factor = (
            params["longest_road"] if num_buildable_nodes == 0 else 0.1
        )

        return float(
            game.state.player_state[f"{key}_VICTORY_POINTS"] * params["public_vps"]
            + production * params["production"]
            + enemy_production * params["enemy_production"]
            + reachable_production_at_zero * params["reachable_production_0"]
            + reachable_production_at_one * params["reachable_production_1"]
            + hand_synergy * params["hand_synergy"]
            + num_buildable_nodes * params["buildable_nodes"]
            + num_tiles * params["num_tiles"]
            + num_in_hand * params["hand_resources"]
            + discard_penalty
            + longest_road_length * longest_road_factor
            + player_num_dev_cards(game.state, p0_color) * params["hand_devs"]
            + get_played_dev_cards(game.state, p0_color, "KNIGHT") * params["army_size"]
        )

    return fn


def value_production(sample, player_name="P0", include_variety=True):
    proba_point = 2.778 / 100
    features = [
        f"EFFECTIVE_{player_name}_WHEAT_PRODUCTION",
        f"EFFECTIVE_{player_name}_ORE_PRODUCTION",
        f"EFFECTIVE_{player_name}_SHEEP_PRODUCTION",
        f"EFFECTIVE_{player_name}_WOOD_PRODUCTION",
        f"EFFECTIVE_{player_name}_BRICK_PRODUCTION",
    ]
    prod_sum = sum([sample[f] for f in features])
    prod_variety = (
        sum([sample[f] != 0 for f in features]) * TRANSLATE_VARIETY * proba_point
    )
    return prod_sum + (0 if not include_variety else prod_variety)


def contender_fn(params):
    return base_fn(params or CONTENDER_WEIGHTS)


ALPHABETA_DEFAULT_DEPTH = 2
MAX_SEARCH_TIME_SECS = 20


class AlphaBetaPlayer(Player):
    """
    Player that executes an AlphaBeta Search where the value of each node
    is taken to be the expected value (using the probability of rolls, etc...)
    of its children. At leafs we simply use the heuristic function given.

    NOTE: More than 3 levels seems to take much longer, it would be
    interesting to see this with prunning.
    """

    def __init__(
        self,
        color,
        depth=ALPHABETA_DEFAULT_DEPTH,
        prunning=False,
        value_fn_builder_name=None,
        params=DEFAULT_WEIGHTS,
        epsilon=None,
    ):
        super().__init__(color)
        self.depth = int(depth)
        self.prunning = str(prunning).lower() != "false"
        self.value_fn_builder_name = (
            "contender_fn" if value_fn_builder_name == "C" else "base_fn"
        )
        self.params = params
        self.use_value_function = None
        self.epsilon = epsilon

    def value_function(self, game, p0_color):
        raise NotImplementedError

    def get_actions(self, game):
        if self.prunning:
            return list_prunned_actions(game)
        return game.state.playable_actions

    def decide(self, game: Game, playable_actions):
        actions = self.get_actions(game)
        if len(actions) == 1:
            return actions[0]

        if self.epsilon is not None and random.random() < self.epsilon:
            return random.choice(playable_actions)

        start = time.time()
        state_id = str(len(game.state.actions))
        node = DebugStateNode(state_id, self.color)  # i think it comes from outside
        deadline = start + MAX_SEARCH_TIME_SECS
        result = self.alphabeta(
            game.copy(), self.depth, float("-inf"), float("inf"), deadline, node
        )
        # print("Decision Results:", self.depth, len(actions), time.time() - start)
        # if game.state.num_turns > 10:
        #     render_debug_tree(node)
        #     breakpoint()
        return result[0]

    def __repr__(self) -> str:
        return (
            super().__repr__()
            + f"(depth={self.depth},value_fn={self.value_fn_builder_name},prunning={self.prunning})"
        )

    def alphabeta(self, game, depth, alpha, beta, deadline, node):
        """AlphaBeta MiniMax Algorithm.

        NOTE: Sometimes returns a value, sometimes an (action, value). This is
        because some levels are state=>action, some are action=>state and in
        action=>state would probably need (action, proba, value) as return type.

        {'value', 'action'|None if leaf, 'node' }
        """
        if depth == 0 or game.winning_color() is not None or time.time() >= deadline:
            value_fn = get_value_fn(
                self.value_fn_builder_name,
                self.params,
                self.value_function if self.use_value_function else None,
            )
            value = value_fn(game, self.color)

            node.expected_value = value
            return None, value

        maximizingPlayer = game.state.current_color() == self.color
        actions = self.get_actions(game)  # list of actions.
        action_outcomes = expand_spectrum(game, actions)  # action => (game, proba)[]

        if maximizingPlayer:
            best_action = None
            best_value = float("-inf")
            for i, (action, outcomes) in enumerate(action_outcomes.items()):
                action_node = DebugActionNode(action)

                expected_value = 0
                for j, (outcome, proba) in enumerate(outcomes):
                    out_node = DebugStateNode(
                        f"{node.label} {i} {j}", outcome.state.current_color()
                    )

                    result = self.alphabeta(
                        outcome, depth - 1, alpha, beta, deadline, out_node
                    )
                    value = result[1]
                    expected_value += proba * value

                    action_node.children.append(out_node)
                    action_node.probas.append(proba)

                action_node.expected_value = expected_value
                node.children.append(action_node)

                if expected_value > best_value:
                    best_action = action
                    best_value = expected_value
                alpha = max(alpha, best_value)
                if alpha >= beta:
                    break  # beta cutoff

            node.expected_value = best_value
            return best_action, best_value
        else:
            best_action = None
            best_value = float("inf")
            for i, (action, outcomes) in enumerate(action_outcomes.items()):
                action_node = DebugActionNode(action)

                expected_value = 0
                for j, (outcome, proba) in enumerate(outcomes):
                    out_node = DebugStateNode(
                        f"{node.label} {i} {j}", outcome.state.current_color()
                    )

                    result = self.alphabeta(
                        outcome, depth - 1, alpha, beta, deadline, out_node
                    )
                    value = result[1]
                    expected_value += proba * value

                    action_node.children.append(out_node)
                    action_node.probas.append(proba)

                action_node.expected_value = expected_value
                node.children.append(action_node)

                if expected_value < best_value:
                    best_action = action
                    best_value = expected_value
                beta = min(beta, best_value)
                if beta <= alpha:
                    break  # alpha cutoff

            node.expected_value = best_value
            return best_action, best_value


class DebugStateNode:
    def __init__(self, label, color):
        self.label = label
        self.children = []  # DebugActionNode[]
        self.expected_value = None
        self.color = color


class DebugActionNode:
    def __init__(self, action):
        self.action = action
        self.expected_value: Any = None
        self.children = []  # DebugStateNode[]
        self.probas = []


def render_debug_tree(node):
    from graphviz import Digraph

    dot = Digraph("AlphaBetaSearch")

    agenda = [node]

    while len(agenda) != 0:
        tmp = agenda.pop()
        dot.node(
            tmp.label,
            label=f"<{tmp.label}<br /><font point-size='10'>{tmp.expected_value}</font>>",
            style="filled",
            fillcolor=tmp.color.value,
        )
        for child in tmp.children:
            action_label = (
                f"{tmp.label} - {str(child.action).replace('<', '').replace('>', '')}"
            )
            dot.node(
                action_label,
                label=f"<{action_label}<br /><font point-size='10'>{child.expected_value}</font>>",
                shape="box",
            )
            dot.edge(tmp.label, action_label)
            for action_child, proba in zip(child.children, child.probas):
                dot.node(
                    action_child.label,
                    label=f"<{action_child.label}<br /><font point-size='10'>{action_child.expected_value}</font>>",
                )
                dot.edge(action_label, action_child.label, label=str(proba))
                agenda.append(action_child)
    print(dot.render())


def list_prunned_actions(game):
    current_color = game.state.current_color()
    playable_actions = game.state.playable_actions
    actions = playable_actions.copy()
    types = set(map(lambda a: a.action_type, playable_actions))

    # Prune Initial Settlements at 1-tile places
    if ActionType.BUILD_SETTLEMENT in types and game.state.is_initial_build_phase:
        actions = filter(
            lambda a: len(game.state.board.map.adjacent_tiles[a.value]) != 1, actions
        )

    # Prune Trading if can hold for resources. Only for rare resources.
    if ActionType.MARITIME_TRADE in types:
        port_resources = game.state.board.get_player_port_resources(current_color)
        has_three_to_one = None in port_resources
        # TODO: for 2:1 ports, skip any 3:1 or 4:1 trades
        # TODO: if can_safely_hold, prune all
        tmp_actions = []
        for action in actions:
            if action.action_type != ActionType.MARITIME_TRADE:
                tmp_actions.append(action)
                continue
            # has 3:1, skip any 4:1 trades
            if has_three_to_one and action.value[3] is not None:
                continue
            tmp_actions.append(action)
        actions = tmp_actions

    if ActionType.MOVE_ROBBER in types:
        actions = prune_robber_actions(current_color, game, actions)

    return list(actions)


def prune_robber_actions(current_color, game, actions):
    """Eliminate all but the most impactful tile"""
    enemy_color = next(filter(lambda c: c != current_color, game.state.colors))
    enemy_owned_tiles = set()
    for node_id in get_player_buildings(
        game.state, enemy_color, BuildingType.SETTLEMENT
    ):
        enemy_owned_tiles.update(game.state.board.map.adjacent_tiles[node_id])
    for node_id in get_player_buildings(game.state, enemy_color, BuildingType.CITY):
        enemy_owned_tiles.update(game.state.board.map.adjacent_tiles[node_id])

    robber_moves = set(
        filter(
            lambda a: a.action_type == ActionType.MOVE_ROBBER
            and game.state.board.map.tiles[a.value[0]] in enemy_owned_tiles,
            actions,
        )
    )

    production_features = build_production_features(True)

    def impact(action):
        game_copy = game.copy()
        game_copy.execute(action)

        our_production_sample = production_features(game_copy, current_color)
        enemy_production_sample = production_features(game_copy, current_color)
        production = value_production(our_production_sample, "P0")
        enemy_production = value_production(enemy_production_sample, "P1")

        return enemy_production - production

    most_impactful_robber_action = max(
        robber_moves, key=impact
    )  # most production and variety producing
    actions = filter(
        # lambda a: a.action_type != action_type or a == most_impactful_robber_action,
        lambda a: a.action_type != ActionType.MOVE_ROBBER or a in robber_moves,
        actions,
    )
    return actions
