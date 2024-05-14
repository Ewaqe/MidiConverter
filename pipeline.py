import pretty_midi as midi

import common

from mido import MidiFile
from mido import tempo2bpm, merge_tracks


# Use these parameters for every part of the score
DEFAULT_INSTRUMENT = 'Acoustic Grand Piano'


class SortableNote(midi.Note):
    """Introduce a variant of the Note class to make it sortable."""

    def __init__(self, velocity, pitch, start, end):
        super().__init__(velocity, pitch, start, end)

    def __lt__(self, other):
        return self.start < other.start


def convert_pause_to_string(pause_duration, tempo):
    # Calculate the duration of a single beat in seconds
    beat_duration = 60 / tempo

    # Calculate total pause duration in terms of beats
    total_pause_in_beats = pause_duration / beat_duration

    # Initialize the result string
    result_string = ""

    # Define common musical fractions for simplicity and efficiency
    musical_fractions = [1, 0.5, 0.25, 0.16666666666666666, 0.125, 0.08333333333333333, 0.0625]
    musical_notations = ["1", "2", "4", "6", "8", "12", "16"]

    while total_pause_in_beats > 0:
        for fraction, notation in zip(musical_fractions, musical_notations):
            # Check if the current fraction fits into the remaining pause duration
            if total_pause_in_beats >= fraction:
                # Subtract the fraction from the total pause duration
                total_pause_in_beats -= fraction
                # Append the notation to the result string
                result_string += notation + "p,"
                break
        else:
            # Handle case where no predefined fraction fits
            # This is a fallback and might not be musically accurate for very specific durations
            result_string += "1p,"
            total_pause_in_beats -= 1

    # Remove the trailing comma
    result_string = result_string.rstrip(',')

    return result_string


def notes_to_rttl(part, tempo):
    beat_duration = 60 / tempo * 4
    rttl_string = ":b={},o=0:".format(round(tempo))

    last_note_end = 0

    part.sort(key=lambda x: x.start)
    for note in part:
        if note.start-last_note_end != 0:
            rttl_string += "{},".format(convert_pause_to_string((note.start-last_note_end), tempo))
        last_note_end = note.end
        note_duration = note.end - note.start

        duration = beat_duration / note_duration
        if int((duration % 1)*10) == 5:
            duration = str(int(duration)) + "."
        else:
            duration = round(duration)
        pitch = midi.note_number_to_name(note.pitch).lower()
        rttl_string += "{}{},".format(duration, pitch)
    return rttl_string[:-1]


def generate(filename):

    file_path = filename

    if common.is_invalid_file(file_path):
        return

    # Read MIDi file and clean up
    score = midi.PrettyMIDI(file_path)
    score.remove_invalid_notes()

    # Get tempo in bpm using mido
    for msg in merge_tracks(MidiFile(file_path).tracks):
        if msg.type == 'set_tempo':
            bpm = tempo2bpm(msg.tempo)
            break

    # Get all notes and sort them by start time
    notes = []
    for instrument in score.instruments:
        for note in instrument.notes:
            # Convert Note to SortableNote
            notes.append(SortableNote(note.velocity,
                                      note.pitch,
                                      note.start,
                                      note.end))
    notes.sort()
    notes_count = len(notes)

    # Improved note separation logic
    parts = []
    active_notes = []  # List to keep track of active notes in each part

    for note in notes:
        placed = False
        for i, part in enumerate(parts):
            # Check if the note can be placed in the current part
            can_place = True
            for active_note in active_notes[i]:
                if not (note.end <= active_note.start or note.start >= active_note.end):
                    can_place = False
                    break
            if can_place:
                part.append(note)
                active_notes[i].append(note)
                placed = True
                break
        if not placed:
            # Create a new part if no existing part can accommodate the note
            parts.append([note])
            active_notes.append([note])

    # Improved merging logic
    i = 0
    while i < len(parts) - 1:
        j = i + 1
        while j < len(parts):
            merge_possible = True
            for note_i in parts[i]:
                for note_j in parts[j]:
                    if not (note_i.end <= note_j.start or note_i.start >= note_j.end):
                        merge_possible = False
                        break
                if not merge_possible:
                    break
            if merge_possible:
                # Merge parts[i] and parts[j]
                parts[i].extend(parts[j])
                del parts[j]
                # No need to increment j, as we need to check the new parts[i] with the next part
            else:
                j += 1
        i += 1

    # Sort notes in each part after merging
    for part in parts:
        part.sort(key=lambda x: x.start)


    # Создание RTTL-строк для каждой партии
    rttl_strings = []
    for part in parts:
        rttl_string = notes_to_rttl(part, bpm)
        rttl_strings.append(rttl_string)

    return rttl_strings



if __name__ == '__main__':
    main()