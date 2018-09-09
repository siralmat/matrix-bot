import configparser
import os
import pytest

from unittest.mock import ANY, Mock, patch

from . import zgame as zgame_module
from matrix_bot.modules import base


@pytest.fixture
def root_dir():
    return os.path.abspath(os.path.join(__file__, "../../.."))

@pytest.fixture
def room_id():
    return '!test-room:matrix.thialfihar.org'

@pytest.fixture
def zgame_config(root_dir):
    config = configparser.ConfigParser()
    config.read_string("""
[zgame]
session_dir = {root}/test-data/zgame-sessions
save_dir = {root}/test-data/zgame-savegames

[zgame/make-it-good]
name = Make It Good
file = {root}/test-data/MakeItGood.zblorb
command_prefix = \\n

[zgame/anchor]
name = Anchorhead
file = {root}/test-data/anchor.z8

[zgame/h2g2]
name = Hitchhiker's Guide To The Galaxy
file = {root}/test-data/hhgg.z3
 """.format(root=root_dir))

    return config


@pytest.fixture
def zgame(zgame_config):
    return zgame_module.ZGameModule.create(zgame_config)


def test_default_dfrotz_path(root_dir):
    dfrotz_path = zgame_module.ZGameModule.get_default_dfrotz_path()
    expected_path = os.path.abspath(os.path.join(root_dir, "bin/dfrotz"))
    assert dfrotz_path == expected_path


def test_zgame_config_parsing(zgame, root_dir):
    assert set(zgame.games.keys()) == {'make-it-good', 'anchor', 'h2g2'}

    assert zgame.games['make-it-good']['name'] == "Make It Good"
    assert zgame.games['make-it-good']['file'] == os.path.join(root_dir, "test-data/MakeItGood.zblorb")


def test_zgame_list(zgame, room_id):
    client = Mock()
    event = {
        'origin_server_ts': 1535392295415,
        'sender': '@thi:matrix.thialfihar.org',
        'event_id': '$15353922951493:matrix.thialfihar.org',
        'unsigned': {'age': 23},
        'content': {'body': '!zlist', 'msgtype': 'm.text'},
        'type': 'm.room.message',
        'room_id': room_id,
    }

    room_mock = Mock()
    room_mock.room_id = room_id
    base.Room = Mock()
    base.Room.return_value = room_mock
    zgame.process(client, event)

    base.Room.assert_called_with(client, event['room_id'])
    room_mock.send_html.assert_called_with("""\
<table>
<tr>
<th>id</th>
<th>name</th>
</tr>
<tr>
<td>anchor</td>
<td>Anchorhead</td>
</tr>
<tr>
<td>h2g2</td>
<td>Hitchhiker's Guide To The Galaxy</td>
</tr>
<tr>
<td>make-it-good</td>
<td>Make It Good</td>
</tr>
</table>
""")


def test_zgame_start_without_game_id(zgame, room_id):
    client = Mock()
    event = {
        'origin_server_ts': 1535392295415,
        'sender': '@thi:matrix.thialfihar.org',
        'event_id': '$15353922951493:matrix.thialfihar.org',
        'unsigned': {'age': 23},
        'content': {'body': '!zstart', 'msgtype': 'm.text'},
        'type': 'm.room.message',
        'room_id': room_id,
    }

    room_mock = Mock()
    room_mock.room_id = room_id
    base.Room = Mock()
    base.Room.return_value = room_mock
    zgame.process(client, event)

    base.Room.assert_called_with(client, event['room_id'])
    room_mock.send_text.assert_called_with("Missing argument 'game-id'")


def test_zgame_start_with_unknown_game_id(zgame, room_id):
    client = Mock()
    event = {
        'origin_server_ts': 1535392295415,
        'sender': '@thi:matrix.thialfihar.org',
        'event_id': '$15353922951493:matrix.thialfihar.org',
        'unsigned': {'age': 23},
        'content': {'body': '!zstart foobar', 'msgtype': 'm.text'},
        'type': 'm.room.message',
        'room_id': room_id,
    }

    room_mock = Mock()
    room_mock.room_id = room_id
    base.Room = Mock()
    base.Room.return_value = room_mock
    zgame.process(client, event)

    base.Room.assert_called_with(client, event['room_id'])
    room_mock.send_text.assert_called_with("Bad argument 'game-id': Unknown game-id 'foobar'")


def test_zgame_convert_to_html(zgame):
    data = """\
   Broken Top Boulevard, Outside No. 15                                                                                                Time:  2:26 pm
   - in the black chevy
                                                                                                           [For a closer description of something, EXAMINE it.]
.
     MAKE IT GOOD
        By Jon Ingold

     -- Release 13 / Serial number 090921 / Inform v6.21 Library 6/10

  Broken Top Boulevard, Outside No. 15 (in the black chevy)
  The boulevard through the windscreen is lined with ash trees, thick trunks casting shadows and gnarled roots mangling up the sidewalk. You're sat in your car,
  parked too high up the kerb; just outside the gate to No. 15. Just an ordinary house. With a body inside.

  "Homicide. One Jack Draginam, accountant. Married, no kids. Stabbed. Yadda yadda, blah blah. We got the call from the maid - geez, who has a maid? Apparently
  she wanted to stress there's a lot of blood."

  "Oh, Inspector. Word is, if you don't crack this one, you're out of a job."

  The glove compartment is closed. Sat on the passenger seat is a whiskey bottle.

> > """
    html_data = zgame.convert_to_html(data, "test-room")
    expected_html_data = """\
<div title="[For a closer description of something, EXAMINE it.]">
<div class="location">Broken Top Boulevard, Outside No. 15 (in the black chevy)</div>
<div class="score">Time:  2:26 pm</div>
<p>&#160;  MAKE IT GOOD<br>&#160; &#160; &#160; By Jon Ingold</p>
<p>&#160;  -- Release 13 / Serial number 090921 / Inform v6.21 Library 6/10</p>
<p>The boulevard through the windscreen is lined with ash trees, thick trunks casting shadows and gnarled roots mangling up the sidewalk. You're sat in your car,
parked too high up the kerb; just outside the gate to No. 15. Just an ordinary house. With a body inside.</p>
<p>"Homicide. One Jack Draginam, accountant. Married, no kids. Stabbed. Yadda yadda, blah blah. We got the call from the maid - geez, who has a maid? Apparently
she wanted to stress there's a lot of blood."</p>
<p>"Oh, Inspector. Word is, if you don't crack this one, you're out of a job."</p>
<p>The glove compartment is closed. Sat on the passenger seat is a whiskey bottle.</p>
</div>
"""

    assert html_data == expected_html_data


def test_zgame_convert_to_html_no_status_line(zgame):
    data = """\
You're not holding your gown.

> """
    html_data = zgame.convert_to_html(data, "test-room")
    expected_html_data = """\
<div><p>You're not holding your gown.</p></div>
"""

    assert html_data == expected_html_data


def test_zgame_start_make_it_good(zgame, room_id):
    client = Mock()
    event = {
        'origin_server_ts': 1535392295415,
        'sender': '@thi:matrix.thialfihar.org',
        'event_id': '$15353922951493:matrix.thialfihar.org',
        'unsigned': {'age': 23},
        'content': {'body': '!zstart make-it-good', 'msgtype': 'm.text'},
        'type': 'm.room.message',
        'room_id': room_id,
    }

    zgame.sessions = {}

    room_mock = Mock()
    room_mock.room_id = room_id
    base.Room = Mock()
    base.Room.return_value = room_mock
    zgame.process(client, event)

    base.Room.assert_called_with(client, event['room_id'])
    assert zgame.sessions == {event['room_id']: 'make-it-good'}

def test_zgame_h2g2_list_convert(zgame):
    data = """\
 Bedroom                                                                                                                          Score: 0        Moves: 13

You have:
  a splitting headache
  no tea
  your gown (being worn)

> """

    html_data = zgame.convert_to_html(data, "test-room")
    expected_html_data = """\
<div>
<div class="location">Bedroom</div>\n<div class="score">Score: 0        Moves: 13</div>
<p>You have:<br>&#160; a splitting headache<br>&#160; no tea<br>&#160; your gown (being worn)</p>
</div>
"""

    assert html_data == expected_html_data

def test_zgame_zdirect_on(zgame, room_id):
    client = Mock()
    user_id = '@thi:matrix.thialfihar.org'
    command = '!zdirect on'
    event = {
        'origin_server_ts': 1535392295415,
        'sender': user_id,
        'event_id': '$15353922951493:matrix.thialfihar.org',
        'unsigned': {'age': 23},
        'content': {'body': command, 'msgtype': 'm.text'},
        'type': 'm.room.message',
        'room_id': room_id,
    }

    zgame.direct_mode = {}

    room_mock = Mock()
    room_mock.room_id = room_id
    base.Room = Mock()
    base.Room.return_value = room_mock
    zgame.process(client, event)

    assert zgame.direct_mode == {room_id: {user_id}}

def test_zgame_zdirect_on(zgame, room_id):
    client = Mock()
    user_id = '@thi:matrix.thialfihar.org'
    command = '!zdirect on'
    event = {
        'origin_server_ts': 1535392295415,
        'sender': user_id,
        'event_id': '$15353922951493:matrix.thialfihar.org',
        'unsigned': {'age': 23},
        'content': {'body': command, 'msgtype': 'm.text'},
        'type': 'm.room.message',
        'room_id': room_id,
    }

    zgame.direct_mode = {}

    room_mock = Mock()
    room_mock.room_id = room_id
    base.Room = Mock()
    base.Room.return_value = room_mock
    zgame.process(client, event)

    assert zgame.direct_mode == {room_id: {user_id}}
def test_zgame_zdirect_off_1(zgame, room_id):
    client = Mock()
    user_id = '@thi:matrix.thialfihar.org'
    command = '!zdirect off'
    event = {
        'origin_server_ts': 1535392295415,
        'sender': user_id,
        'event_id': '$15353922951493:matrix.thialfihar.org',
        'unsigned': {'age': 23},
        'content': {'body': command, 'msgtype': 'm.text'},
        'type': 'm.room.message',
        'room_id': room_id,
    }

    zgame.direct_mode = {}

    room_mock = Mock()
    room_mock.room_id = room_id
    base.Room = Mock()
    base.Room.return_value = room_mock
    zgame.process(client, event)

    assert zgame.direct_mode == {}

def test_zgame_zdirect_off_2(zgame, room_id):
    client = Mock()
    user_id = '@thi:matrix.thialfihar.org'
    command = '!zdirect off'
    event = {
        'origin_server_ts': 1535392295415,
        'sender': user_id,
        'event_id': '$15353922951493:matrix.thialfihar.org',
        'unsigned': {'age': 23},
        'content': {'body': command, 'msgtype': 'm.text'},
        'type': 'm.room.message',
        'room_id': room_id,
    }

    zgame.direct_mode = {room_id: {user_id}}

    room_mock = Mock()
    room_mock.room_id = room_id
    base.Room = Mock()
    base.Room.return_value = room_mock
    zgame.process(client, event)

    assert zgame.direct_mode == {room_id: set()}

def test_zgame_room_message_direct_command(zgame, room_id):
    client = Mock()
    user_id = '@thi:matrix.thialfihar.org'
    command = 'examine'
    event = {
        'origin_server_ts': 1535392295415,
        'sender': user_id,
        'event_id': '$15353922951493:matrix.thialfihar.org',
        'unsigned': {'age': 23},
        'content': {'body': command, 'msgtype': 'm.text'},
        'type': 'm.room.message',
        'room_id': room_id,
    }

    zgame.direct_mode = {room_id: user_id}

    room_mock = Mock()
    room_mock.room_id = room_id
    base.Room = Mock()
    base.Room.return_value = room_mock

    zgame.zcommand = Mock()

    zgame.process(client, event)

    zgame.zcommand.assert_called_with(event, command, room_=ANY, user_=ANY)
